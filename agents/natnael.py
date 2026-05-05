"""
# Agent: Natnael (Infrastructure & Testing)
#
# ናትናኤል — "Gift of God" in Amharic/Hebrew. Natnael is the glue.
# He sets everything up, keeps the repo green, and runs the final
# integration gauntlet. He's the last line of defense before shipping.
# He monitors ALL integration signals from other agents and
# triggers the end-to-end test suite when all features are ready.
#
# Responsibilities:
#   - All code in setup.cfg, pyproject.toml, tests/unit/*, tests/integration/*
#   - Phases 1 and 10 from tasks/infra.md
#   - README, gzip support, --max-matches, full E2E test suite
#
# Tools Available:
#   - Read/write: setup.cfg, pyproject.toml, tests/*, README.md
#   - Test runner: full pytest suite + coverage
#   - Matrix rooms: #mzgb-infra, #mzgb-integration, #mzgb-general
#
# Interfaces:
#   - Starts Phase 1 immediately (no dependencies)
#   - Listens for READY signals from all agents on #mzgb-integration
#   - Posts "PHASE-10-START" to #general when all features confirmed
#   - Posts final "SHIP-READY ✓" to #general when Phase 10 passes
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
logger = logging.getLogger("natnael")

ME = AGENTS["natnael"]
TRACK = TASK_FILES["infra"]
ROOT = Path(__file__).parent.parent

ALL_FEATURE_SIGNALS = {"filter-engine", "cli-mvp", "all-features"}


async def run_full_suite() -> tuple[bool, str]:
    """Run the complete test suite with coverage."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short",
         "--cov=mzgb", "--cov-report=term-missing:skip-covered"],
        capture_output=True, text=True, cwd=ROOT
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


async def monitor_integration_signals(matrix: AgentMatrixClient) -> None:
    """Listen on #integration and post a summary table of what's ready."""
    received = set()

    async def on_message(sender: str, body: str):
        for signal in ALL_FEATURE_SIGNALS:
            if signal in body and "READY:" in body and signal not in received:
                received.add(signal)
                await matrix.send(
                    ROOMS["infra"],
                    f"📡 Natnael | Signal received: READY: {signal}\n"
                    f"  Progress: {len(received)}/{len(ALL_FEATURE_SIGNALS)} signals"
                )

    asyncio.create_task(matrix.listen(ROOMS["integration"], on_message))


async def work_cycle(matrix: AgentMatrixClient) -> None:
    """Phase 1 first, then monitor until all features ready, then Phase 10."""
    # Phase 1 — no dependencies, start immediately
    while True:
        task = next_task(TRACK)
        if task is None or task.phase > 1:
            await matrix.send(ROOMS["infra"], "✅ Phase 1 scaffold complete — waiting for all features before Phase 10.")
            break

        await matrix.send_status(ROOMS["infra"], f"STARTING task {task.id}", task.description)
        await matrix.send(
            ROOMS["infra"],
            f"🏗️  [{task.id}] Implementing: {task.description}\n"
            f"  Files: pyproject.toml | setup.cfg | mzgb/__init__.py\n"
            f"  Reply DONE:{task.id} to confirm."
        )

        done_event = asyncio.Event()

        async def on_confirm(sender: str, body: str):
            if f"DONE:{task.id}" in body:
                done_event.set()

        listen_task = asyncio.create_task(matrix.listen(ROOMS["infra"], on_confirm))
        await done_event.wait()
        listen_task.cancel()

        mark_done(TRACK, task.id)
        await matrix.send_status(ROOMS["infra"], f"DONE ✓ task {task.id}",
                                  f"{summary(TRACK)['done']}/{summary(TRACK)['total']} done.")
        await asyncio.sleep(2)

    # Wait for all-features signal from Tigist
    await matrix.send(ROOMS["integration"],
        "⏳ Natnael waiting for READY: all-features before triggering Phase 10 + final E2E suite.")
    all_ready = asyncio.Event()

    async def on_all_features(sender: str, body: str):
        if "all-features" in body and "READY:" in body:
            all_ready.set()

    listen_task = asyncio.create_task(matrix.listen(ROOMS["integration"], on_all_features))
    await all_ready.wait()
    listen_task.cancel()

    await matrix.send(ROOMS["general"],
        "🚀 PHASE-10-START | All features confirmed. Natnael starting Phase 10: polish, tests, README.")

    # Phase 10
    while True:
        task = next_task(TRACK)
        if task is None:
            break

        await matrix.send_status(ROOMS["infra"], f"STARTING task {task.id}", task.description)
        await matrix.send(
            ROOMS["infra"],
            f"📦 [{task.id}] Implementing: {task.description}\n  Reply DONE:{task.id} to confirm."
        )

        done_event = asyncio.Event()

        async def on_confirm2(sender: str, body: str):
            if f"DONE:{task.id}" in body:
                done_event.set()

        listen_task = asyncio.create_task(matrix.listen(ROOMS["infra"], on_confirm2))
        await done_event.wait()
        listen_task.cancel()
        mark_done(TRACK, task.id)
        await asyncio.sleep(2)

    # Final E2E gate
    passed, output = await run_full_suite()
    if passed:
        await matrix.send(ROOMS["general"],
            "✅ SHIP-READY ✓ | Natnael — full test suite green, coverage threshold met.\n"
            "  mzgb is ready to release! 🎉")
    else:
        await matrix.send(ROOMS["blockers"],
            f"🚨 Natnael | Final E2E suite FAILED\n```\n{output[:1200]}\n```")


async def main():
    matrix = AgentMatrixClient(
        homeserver=MATRIX_HOMESERVER,
        username=ME["username"],
        password=ME["password"],
        display_name=ME["display_name"],
    )
    await matrix.connect()

    for room in [ROOMS["infra"], ROOMS["integration"], ROOMS["blockers"], ROOMS["general"]]:
        await matrix.join_room(room)

    await monitor_integration_signals(matrix)

    s = summary(TRACK)
    await matrix.send(
        ROOMS["general"],
        f"👋 Selam! Natnael here (Infra & Testing). Online.\n"
        f"  Track: infra.md | {s['done']}/{s['total']} tasks | {s['pending']} pending.\n"
        f"  I own: scaffold, packaging, tests, README (Phases 1 + 10)\n"
        f"  Starting Phase 1 now. I'll run the final E2E gate when all features land."
    )

    await run_autonomous_loop(matrix, track="infra", track_room=ROOMS["infra"], agent_name="natnael")


if __name__ == "__main__":
    asyncio.run(main())
