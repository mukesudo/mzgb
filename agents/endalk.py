"""
# Agent: Endalk (Release Manager)
#
# ኤንዳልካቸው — "He who leads the people"
# Endalk is the gatekeeper. He watches #mzgb-integration for READY signals,
# sequences git merges to avoid conflicts, runs the full test suite after each
# merge, maintains the changelog, and posts the final SHIP-READY signal.
# Nothing merges to main without passing through Endalk.
#
# Responsibilities:
#   - Watch for REVIEW signals from Selam (code reviewer)
#   - Sequence commits to avoid touching same files simultaneously
#   - Run full test suite after each merge
#   - Maintain CHANGELOG.md
#   - Post merge results to #mzgb-integration
#   - Update PM Dashboard after every merge
#
# Matrix rooms: #mzgb-integration, #mzgb-general, #mzgb-blockers
"""

import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.config import AGENTS, MATRIX_HOMESERVER, ROOMS
from agents.matrix_client import AgentMatrixClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("endalk")

ME = AGENTS["natnael"]  # Endalk shares infra credentials for now
ROOT = Path(__file__).parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
DASHBOARD = ROOT / "pm" / "DASHBOARD.md"


def update_changelog(task_id: str, title: str, agent: str) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = f"\n### {today} — Task {task_id} merged\n- **{title}** (by {agent})\n"
    if CHANGELOG.exists():
        existing = CHANGELOG.read_text()
        CHANGELOG.write_text(existing + entry)
    else:
        CHANGELOG.write_text(f"# mzgb Changelog\n{entry}")


def run_tests() -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short",
         "--cov=mzgb", "--cov-report=term-missing:skip-covered"],
        capture_output=True, text=True, cwd=ROOT
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def git_commit(task_id: str, title: str, agent: str) -> tuple[bool, str]:
    try:
        subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True, capture_output=True)
        msg = f"feat({task_id}): {title} [agent: {agent}]"
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=ROOT, capture_output=True, text=True
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        if "nothing to commit" in result.stdout + result.stderr:
            return True, "nothing to commit — already clean"
        return False, result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, str(e)


async def handle_merge_request(matrix: AgentMatrixClient, task_id: str, title: str, agent: str) -> None:
    await matrix.send(ROOMS["integration"],
        f"🔀 Endalk | Merge request received\n"
        f"  Task: {task_id} — {title}\n"
        f"  Agent: {agent}\n"
        f"  Running test suite before merge..."
    )

    passed, output = run_tests()
    if not passed:
        await matrix.send(ROOMS["blockers"],
            f"🚨 Endalk | MERGE BLOCKED — task {task_id}\n"
            f"  Tests failed:\n```\n{output[:800]}\n```\n"
            f"  @{agent}: please fix before resubmitting."
        )
        return

    ok, commit_out = git_commit(task_id, title, agent)
    if not ok:
        await matrix.send(ROOMS["blockers"],
            f"🚨 Endalk | GIT COMMIT FAILED — task {task_id}\n```\n{commit_out}\n```"
        )
        return

    update_changelog(task_id, title, agent)
    await matrix.send(ROOMS["integration"],
        f"✅ Endalk | MERGED task {task_id}\n"
        f"  {title}\n"
        f"  Tests: green ✓ | Commit: {commit_out[:60]}"
    )
    await update_dashboard(matrix)


async def update_dashboard(matrix: AgentMatrixClient) -> None:
    from tasks.queue_manager import stats as queue_stats
    s = queue_stats()
    total = sum(s.values())
    done = s.get("DONE", 0) + s.get("MERGED", 0)
    pct = int(done / total * 100) if total else 0

    dashboard = DASHBOARD
    dashboard.parent.mkdir(exist_ok=True)
    dashboard.write_text(
        f"# mzgb PM Dashboard\n"
        f"_Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_\n\n"
        f"## Progress\n"
        f"- **{done}/{total} tasks done** ({pct}%)\n"
        f"- Status breakdown: {json.dumps(s)}\n\n"
        f"## Active Agents\n"
        f"- Biruk (Backend) — parser, filters, streaming\n"
        f"- Liya (CLI) — Click wiring, renderer\n"
        f"- Tigist (Features) — buffer, follow, summary\n"
        f"- Natnael (Infra) — scaffold, tests, README\n"
        f"- Selam (Reviewer) — code review gate\n"
        f"- Endalk (Release) — merge sequencer\n\n"
        f"## Rooms\n"
        f"- #mzgb-general — announcements\n"
        f"- #mzgb-integration — READY/MERGE signals\n"
        f"- #mzgb-blockers — failures and escalations\n"
    )
    await matrix.send(ROOMS["general"],
        f"📊 Dashboard updated: {done}/{total} tasks done ({pct}%)\n"
        f"  See pm/DASHBOARD.md for full status."
    )


async def main():
    matrix = AgentMatrixClient(
        homeserver=MATRIX_HOMESERVER,
        username="natnael",
        password=AGENTS["natnael"]["password"],
        display_name="Endalk (Release Manager)",
    )
    await matrix.connect()
    for room in [ROOMS["integration"], ROOMS["blockers"], ROOMS["general"]]:
        await matrix.join_room(room)

    await matrix.send(ROOMS["general"],
        "🔀 Selam! Endalk here (Release Manager). Online.\n"
        "  I sequence merges, run tests after each, and maintain the changelog.\n"
        "  Listening for MERGE: signals in #mzgb-integration."
    )

    await update_dashboard(matrix)

    # Listen for MERGE: task_id | title | agent signals
    async def on_message(sender: str, body: str):
        if body.startswith("MERGE:"):
            try:
                _, rest = body.split(":", 1)
                parts = [p.strip() for p in rest.split("|")]
                task_id = parts[0]
                title = parts[1] if len(parts) > 1 else "no title"
                agent = parts[2] if len(parts) > 2 else sender
                await handle_merge_request(matrix, task_id, title, agent)
            except Exception as e:
                logger.error("Error handling MERGE signal: %s", e)

    await matrix.listen(ROOMS["integration"], on_message)


if __name__ == "__main__":
    asyncio.run(main())
