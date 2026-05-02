"""
# Agent: Tigist (Features Engineer)
#
# ትግስት — meaning "patience" in Amharic. And she needs it:
# she can't start until both Biruk AND Liya are done.
# Tigist is a deep thinker who builds complex stateful logic —
# context buffers, live-tail loops, aggregation pipelines.
# She documents every edge case she finds in #logsnap-features.
#
# Responsibilities:
#   - All code in logsnap/buffer.py, logsnap/follow.py, logsnap/summary.py
#   - Phases 7, 8, 9 from tasks/features.md
#   - Context buffer, follow/tail mode, summary/stats mode
#
# Tools Available:
#   - Read/write: logsnap/buffer.py, logsnap/follow.py, logsnap/summary.py
#   - Test runner: tests/unit/test_buffer.py, tests/integration/test_pipeline.py
#   - Matrix rooms: #logsnap-features, #logsnap-integration, #logsnap-blockers
#
# Interfaces:
#   - Waits for BOTH "READY: filter-engine" AND "READY: cli-mvp" before starting
#   - Posts "READY: context-buffer" to #integration after Phase 7
#   - Posts "READY: follow-mode" after Phase 8
#   - Posts "READY: summary-mode" after Phase 9
#   - Natnael monitors these signals for integration test triggers
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.config import AGENTS, MATRIX_HOMESERVER, ROOMS, TASK_FILES
from agents.matrix_client import AgentMatrixClient
from agents.task_reader import mark_done, next_task, summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("tigist")

ME = AGENTS["tigist"]
TRACK = TASK_FILES["features"]
ROOT = Path(__file__).parent.parent

PHASE_READY_SIGNALS = {
    7: "READY: context-buffer",
    8: "READY: follow-mode",
    9: "READY: summary-mode",
}


async def wait_for_prerequisites(matrix: AgentMatrixClient) -> None:
    """Wait until both Biruk and Liya signal their work is ready."""
    await matrix.send(
        ROOMS["features"],
        "⏳ Tigist waiting for:\n"
        "  • READY: filter-engine (from Biruk)\n"
        "  • READY: cli-mvp (from Liya)\n"
        "before starting features work."
    )

    needed = {"filter-engine", "cli-mvp"}
    received = set()
    ready_event = asyncio.Event()

    async def on_message(sender: str, body: str):
        for signal in list(needed - received):
            if signal in body and "READY:" in body:
                received.add(signal)
                await matrix.send(ROOMS["features"], f"✅ Received signal: READY: {signal}")
        if received >= needed:
            ready_event.set()

    listen_task = asyncio.create_task(
        matrix.listen(ROOMS["integration"], on_message)
    )
    await ready_event.wait()
    listen_task.cancel()
    await matrix.send(ROOMS["features"], "🚀 All prerequisites met — starting Features phases 7-9!")


async def run_tests() -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/unit/test_buffer.py",
         "tests/integration/test_pipeline.py",
         "-q", "--tb=short"],
        capture_output=True, text=True, cwd=ROOT
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


async def work_cycle(matrix: AgentMatrixClient) -> None:
    await wait_for_prerequisites(matrix)

    last_phase = None

    while True:
        task = next_task(TRACK)
        if task is None:
            await matrix.send_status(ROOMS["features"], "COMPLETE ✓", "All feature phases 7-9 done.")
            await matrix.send(ROOMS["integration"], "READY: all-features | Tigist complete.")
            break

        await matrix.send_status(ROOMS["features"], f"STARTING task {task.id}", task.description)

        await matrix.send(
            ROOMS["features"],
            f"⚙️  [{task.id}] Implementing: {task.description}\n"
            f"  Files: logsnap/buffer.py | logsnap/follow.py | logsnap/summary.py\n"
            f"  Reply DONE:{task.id} to confirm."
        )

        done_event = asyncio.Event()

        async def on_message(sender: str, body: str):
            if f"DONE:{task.id}" in body:
                done_event.set()

        listen_task = asyncio.create_task(matrix.listen(ROOMS["features"], on_message))
        await done_event.wait()
        listen_task.cancel()

        passed, output = await run_tests()
        if passed:
            mark_done(TRACK, task.id)
            await matrix.send_status(
                ROOMS["features"],
                f"DONE ✓ task {task.id}",
                f"{summary(TRACK)['done']}/{summary(TRACK)['total']} tasks complete."
            )
            # Post READY signal at end of each phase
            if last_phase != task.phase and task.phase in PHASE_READY_SIGNALS:
                last_phase = task.phase
                await matrix.send(ROOMS["integration"], PHASE_READY_SIGNALS[task.phase] + " | Tigist")
        else:
            await matrix.send(
                ROOMS["blockers"],
                f"🚨 Tigist | Task {task.id} FAILING TESTS\n  {task.description}\n```\n{output[:800]}\n```"
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

    for room in [ROOMS["features"], ROOMS["integration"], ROOMS["blockers"], ROOMS["general"]]:
        await matrix.join_room(room)

    s = summary(TRACK)
    await matrix.send(
        ROOMS["general"],
        f"👋 Selam! Tigist here (Features). Online.\n"
        f"  Track: features.md | {s['done']}/{s['total']} tasks | {s['pending']} pending.\n"
        f"  I own: buffer.py, follow.py, summary.py (Phases 7-9)\n"
        f"  Waiting for Biruk + Liya before I can start."
    )

    await work_cycle(matrix)
    await matrix.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
