"""
# Agent: Biruk (Backend Engineer)
#
# ብርሃን ለሁሉ — "Light for all"
# Biruk means "blessed" in Amharic. He's methodical, precise, and never
# ships without understanding the full pipeline. He reads specs carefully
# before writing a single line and posts blockers immediately.
#
# Responsibilities:
#   - All code in logsnap/parser.py, logsnap/filters.py, logsnap/cli.py (stream_lines)
#   - Phases 2, 3, 4 from tasks/backend.md
#   - Unblocks Liya (CLI) and Tigist (Features) by completing the core pipeline
#
# Tools Available:
#   - Read/write: logsnap/parser.py, logsnap/filters.py, logsnap/cli.py
#   - Test runner: tests/unit/test_parser.py, tests/unit/test_filters.py
#   - Matrix rooms: #logsnap-backend, #logsnap-integration, #logsnap-blockers
#
# Interfaces:
#   - Posts "READY: <module>" to #logsnap-integration when a phase is done
#   - Listens on #logsnap-backend for spec clarifications
#   - Posts to #logsnap-blockers if a design decision is unclear
#   - Liya listens for "READY: filters" before wiring CLI flags
#   - Tigist listens for "READY: filters" before starting Phase 7
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.autonomous_loop import run_autonomous_loop
from agents.config import AGENTS, MATRIX_HOMESERVER, ROOMS
from agents.matrix_client import AgentMatrixClient
from tasks.queue_manager import stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("biruk")

ME = AGENTS["biruk"]
ROOT = Path(__file__).parent.parent


from typing import Tuple

async def run_tests() -> Tuple[bool, str]:
    """Run backend unit tests. Returns (passed, output)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/test_parser.py",
         "tests/unit/test_filters.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=ROOT
    )
    passed = result.returncode == 0
    output = (result.stdout + result.stderr).strip()
    return passed, output


async def work_cycle(matrix: AgentMatrixClient) -> None:
    """Pick next task → implement → test → mark done → post update. Repeat."""
    while True:
        task = next_task(TRACK)
        if task is None:
            await matrix.send_status(
                ROOMS["backend"],
                "COMPLETE ✓",
                "All backend tasks done. Phases 2-4 complete."
            )
            await matrix.send(ROOMS["integration"],
                "READY: stream-engine filter-engine log-parser | Biruk has completed all backend phases.")
            break

        await matrix.send_status(
            ROOMS["backend"],
            f"STARTING task {task.id}",
            task.description
        )
        logger.info("Working on task %s: %s", task.id, task.description)

        # ── Pause here for actual implementation by AI/human ──────────────────
        # In a real agentic loop, the LLM would generate the implementation.
        # For now, we signal that the task is queued and wait for confirmation.
        await matrix.send(
            ROOMS["backend"],
            f"🔧 [{task.id}] Implementing: {task.description}\n"
            f"  Files: logsnap/parser.py | logsnap/filters.py | logsnap/cli.py\n"
            f"  Reply DONE:{task.id} when implementation is confirmed."
        )

        # Wait for a human or orchestrator to confirm via Matrix
        done_event = asyncio.Event()

        async def on_message(sender: str, body: str):
            if f"DONE:{task.id}" in body:
                done_event.set()

        listen_task = asyncio.create_task(
            matrix.listen(ROOMS["backend"], on_message)
        )
        await done_event.wait()
        listen_task.cancel()

        # Run tests
        passed, output = await run_tests()
        if passed:
            mark_done(TRACK, task.id)
            await matrix.send_status(
                ROOMS["backend"],
                f"DONE ✓ task {task.id}",
                f"Tests green. {summary(TRACK)['done']}/{summary(TRACK)['total']} tasks complete."
            )
        else:
            await matrix.send(
                ROOMS["blockers"],
                f"🚨 Biruk | Task {task.id} FAILING TESTS\n"
                f"  {task.description}\n"
                f"```\n{output[:800]}\n```"
            )
            logger.error("Tests failed for task %s", task.id)
            await asyncio.sleep(30)

        await asyncio.sleep(2)


async def main():
    matrix = AgentMatrixClient(
        homeserver=MATRIX_HOMESERVER,
        username=ME["username"],
        password=ME["password"],
        display_name=ME["display_name"],
    )
    await matrix.connect()

    for room in [ROOMS["backend"], ROOMS["integration"], ROOMS["blockers"], ROOMS["general"]]:
        await matrix.join_room(room)

    s = stats()
    await matrix.send(
        ROOMS["general"],
        f"👋 Biruk here (Backend). Online and ready.\n"
        f"  Track: backend | {s.get('DONE', 0)} done, {s.get('OPEN', 0)} open.\n"
        f"  I own: logsnap/parser.py, logsnap/filters.py, stream_lines()\n"
        f"  Autonomous mode ON - claiming tasks from queue."
    )

    await run_autonomous_loop(matrix, track="backend", track_room=ROOMS["backend"], agent_name="biruk")


if __name__ == "__main__":
    asyncio.run(main())
