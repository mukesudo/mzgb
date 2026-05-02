"""
# Agent: Selam (Code Reviewer)
#
# ሰላም — "Peace" in Amharic. Also the most common greeting.
# Selam reviews every implementation before it reaches Endalk.
# She is methodical, consistent, and never approves code she hasn't read.
# She checks style, test coverage, and anti-patterns — then either
# approves (posts MERGE: to #integration) or posts review comments.
#
# Responsibilities:
#   - Listen for REVIEW: signals from implementation agents
#   - Check that tests exist and pass for the task
#   - Check for common anti-patterns (hardcoded paths, bare except, etc.)
#   - Approve → post MERGE: to #logsnap-integration
#   - Request changes → post back to agent's room
#
# Matrix rooms: #logsnap-integration, #logsnap-blockers, all agent rooms
"""

import asyncio
import ast
import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.config import AGENTS, MATRIX_HOMESERVER, ROOMS
from agents.matrix_client import AgentMatrixClient
from tasks.queue_manager import approve, _load

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("selam")

ROOT = Path(__file__).parent.parent

ANTI_PATTERNS = [
    ("bare except", "except:"),
    ("hardcoded /tmp path", '"/tmp/'),
    ("print() instead of logger", "\nprint("),
    ("TODO left in code", "# TODO"),
]


def find_task(task_id: str) -> dict | None:
    data = _load()
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def check_syntax(files: list[str]) -> list[str]:
    issues = []
    for f in files:
        path = ROOT / f
        if not path.exists() or not f.endswith(".py"):
            continue
        try:
            ast.parse(path.read_text())
        except SyntaxError as e:
            issues.append(f"  ✗ {f}: SyntaxError at line {e.lineno}: {e.msg}")
    return issues


def check_anti_patterns(files: list[str]) -> list[str]:
    issues = []
    for f in files:
        path = ROOT / f
        if not path.exists() or not f.endswith(".py"):
            continue
        content = path.read_text()
        for name, pattern in ANTI_PATTERNS:
            if pattern in content:
                issues.append(f"  ⚠ {f}: {name} detected")
    return issues


def run_relevant_tests(track: str) -> tuple[bool, str]:
    test_map = {
        "backend": ["tests/unit/test_parser.py", "tests/unit/test_filters.py"],
        "cli": ["tests/e2e/test_cli.py"],
        "features": ["tests/unit/test_buffer.py", "tests/integration/test_pipeline.py"],
        "infra": ["tests/"],
    }
    test_paths = test_map.get(track, ["tests/"])
    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + test_paths + ["-q", "--tb=short"],
        capture_output=True, text=True, cwd=ROOT
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


async def review_task(matrix: AgentMatrixClient, task_id: str, agent: str) -> None:
    task = find_task(task_id)
    if not task:
        await matrix.send(ROOMS["blockers"], f"🚨 Selam | Unknown task ID: {task_id}")
        return

    files = task.get("files", [])
    track = task.get("track", "backend")
    title = task["title"]

    await matrix.send(ROOMS["integration"],
        f"🔍 Selam | Reviewing task {task_id}\n"
        f"  {title}\n"
        f"  Files: {', '.join(files)}"
    )

    issues = []

    # 1. Syntax check
    syntax_issues = check_syntax(files)
    issues.extend(syntax_issues)

    # 2. Anti-pattern check
    pattern_issues = check_anti_patterns(files)
    issues.extend(pattern_issues)

    # 3. Run tests
    tests_passed, test_output = run_relevant_tests(track)
    if not tests_passed:
        issues.append(f"  ✗ Tests failing:\n```\n{test_output[:600]}\n```")

    if issues:
        agent_room = ROOMS.get(track, ROOMS["blockers"])
        await matrix.send(agent_room,
            f"🔄 Selam → {agent} | REVIEW COMMENTS for task {task_id}\n"
            + "\n".join(issues)
            + f"\n\nPlease fix and repost REVIEW:{task_id}|{agent}"
        )
        return

    # Approved
    approve(task_id)
    await matrix.send(ROOMS["integration"],
        f"✅ Selam | APPROVED task {task_id} — {title}\n"
        f"MERGE:{task_id}|{title}|{agent}"
    )


async def main():
    matrix = AgentMatrixClient(
        homeserver=MATRIX_HOMESERVER,
        username="biruk",
        password=AGENTS["biruk"]["password"],
        display_name="Selam (Code Reviewer)",
    )
    await matrix.connect()
    for room in list(ROOMS.values()):
        await matrix.join_room(room)

    await matrix.send(ROOMS["general"],
        "🔍 Selam! Selam here (Code Reviewer). Online.\n"
        "  I review every implementation before it reaches Endalk.\n"
        "  Post REVIEW:task_id|agent_name in any room to trigger a review."
    )

    async def on_message(sender: str, body: str):
        if body.startswith("REVIEW:") and "|" in body:
            try:
                _, rest = body.split(":", 1)
                parts = [p.strip() for p in rest.split("|")]
                task_id = parts[0]
                agent = parts[1] if len(parts) > 1 else sender
                await review_task(matrix, task_id, agent)
            except Exception as e:
                logger.error("Review error: %s", e)

    # Listen on all rooms
    for room_alias in ROOMS.values():
        matrix.client.add_event_callback(
            lambda room, event, ra=room_alias: asyncio.create_task(
                on_message(event.sender, event.body)
            ) if hasattr(event, "body") and event.sender != f"@biruk:localhost" else None,
            __import__("nio").RoomMessageText
        )

    await matrix.client.sync_forever(timeout=30000, full_state=True)


if __name__ == "__main__":
    asyncio.run(main())
