"""
# Agent: Liya (CLI & Output Renderer)
#
# ልያ — meaning "great one" in Amharic/Tigrinya.
# Liya has an eye for UX. She cares deeply about how things look and feel.
# She won't wire a flag until the backend it depends on is confirmed ready.
# She posts API contracts to #mzgb-integration before starting work.
#
# Responsibilities:
#   - All code in mzgb/cli.py (Click commands), mzgb/renderer.py
#   - Phases 1, 5, 6 from tasks/cli.md
#   - The --help text, color output, TTY detection, match highlighting
#
# Tools Available:
#   - Read/write: mzgb/cli.py, mzgb/renderer.py
#   - Test runner: tests/e2e/test_cli.py
#   - Matrix rooms: #mzgb-cli, #mzgb-integration, #mzgb-blockers
#
# Interfaces:
#   - Waits for "READY: filter-engine" from Biruk before wiring Phase 5
#   - Posts "READY: cli-mvp" to #mzgb-integration after Phase 5
#   - Tigist listens for "READY: cli-mvp" before starting Phase 7
#   - Posts color/output API contracts to #mzgb-integration for Tigist
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.autonomous_loop import run_autonomous_loop
from agents.config import AGENTS, MATRIX_HOMESERVER, ROOMS, TASK_FILES
from agents.matrix_client import AgentMatrixClient
from agents.task_reader import mark_done, next_task, summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("liya")

ME = AGENTS["liya"]
TRACK = TASK_FILES["cli"]
ROOT = Path(__file__).parent.parent


async def wait_for_backend_ready(matrix: AgentMatrixClient) -> None:
    """Block until Biruk posts READY: filter-engine to #integration."""
    await matrix.send(
        ROOMS["cli"],
        "⏳ Liya waiting for READY: filter-engine from Biruk before wiring Phase 5 flags."
    )
    ready_event = asyncio.Event()

    async def on_message(sender: str, body: str):
        if "READY:" in body and "filter-engine" in body:
            ready_event.set()

    listen_task = asyncio.create_task(
        matrix.listen(ROOMS["integration"], on_message)
    )
    await ready_event.wait()
    listen_task.cancel()
    await matrix.send(ROOMS["cli"], "✅ filter-engine ready — starting Phase 5 MVP wiring.")


async def run_tests() -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/e2e/test_cli.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=ROOT
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


async def work_cycle(matrix: AgentMatrixClient) -> None:
    backend_unblocked = False

    while True:
        task = next_task(TRACK)
        if task is None:
            await matrix.send_status(ROOMS["cli"], "COMPLETE ✓", "All CLI tasks done. Phases 1, 5-6 complete.")
            await matrix.send(ROOMS["integration"],
                "READY: cli-mvp renderer | Liya has completed CLI wiring and output renderer.")
            break

        # Phase 5+ requires backend to be ready first
        if task.phase >= 5 and not backend_unblocked:
            await wait_for_backend_ready(matrix)
            backend_unblocked = True

        await matrix.send_status(ROOMS["cli"], f"STARTING task {task.id}", task.description)

        await matrix.send(
            ROOMS["cli"],
            f"🎨 [{task.id}] Implementing: {task.description}\n"
            f"  Files: mzgb/cli.py | mzgb/renderer.py\n"
            f"  Reply DONE:{task.id} to confirm."
        )

        done_event = asyncio.Event()

        async def on_message(sender: str, body: str):
            if f"DONE:{task.id}" in body:
                done_event.set()

        listen_task = asyncio.create_task(matrix.listen(ROOMS["cli"], on_message))
        await done_event.wait()
        listen_task.cancel()

        passed, output = await run_tests()
        if passed:
            mark_done(TRACK, task.id)
            await matrix.send_status(
                ROOMS["cli"],
                f"DONE ✓ task {task.id}",
                f"{summary(TRACK)['done']}/{summary(TRACK)['total']} tasks complete."
            )
        else:
            await matrix.send(
                ROOMS["blockers"],
                f"🚨 Liya | Task {task.id} FAILING TESTS\n  {task.description}\n```\n{output[:800]}\n```"
            )
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

    for room in [ROOMS["cli"], ROOMS["integration"], ROOMS["blockers"], ROOMS["general"]]:
        await matrix.join_room(room)

    s = summary(TRACK)
    await matrix.send(
        ROOMS["general"],
        f"👋 Selam! Liya here (CLI & Renderer). Online and ready.\n"
        f"  Track: cli.md | {s['done']}/{s['total']} tasks done | {s['pending']} pending.\n"
        f"  I own: mzgb/cli.py, mzgb/renderer.py\n"
        f"  Waiting for Biruk's filter-engine before I wire Phase 5 flags."
    )

    await run_autonomous_loop(matrix, track="cli", track_room=ROOMS["cli"], agent_name="liya")


if __name__ == "__main__":
    asyncio.run(main())
