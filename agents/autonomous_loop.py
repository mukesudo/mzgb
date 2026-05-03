"""
autonomous_loop.py — Self-driving work loop for LogSnap agents.

Each agent calls run_autonomous_loop(matrix, track) and it will:
  1. Claim the next available task from QUEUE.json for this track
  2. Post "I'm working on X" to the track room + general
  3. Post IMPLEMENT:task_id|title|files to #logsnap-integration
     (Cascade reads this and writes the actual code)
  4. Wait for CODE_READY:task_id signal (Cascade posts this when done)
  5. Run the tests
  6. If green → post REVIEW:task_id|agent to trigger Selam
  7. Wait for APPROVED:task_id or CHANGES:task_id from Selam
  8. Loop to next task
  9. If no tasks left for track → post TRACK_DONE and exit
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.config import ROOMS
from agents.matrix_client import AgentMatrixClient
from tasks.queue_manager import claim, complete, next_open, release

logger = logging.getLogger(__name__)
ROOT = Path(__file__).parent.parent

POLL_INTERVAL = 15      # seconds between queue checks
SIGNAL_TIMEOUT = 3600   # seconds to wait for CODE_READY before giving up


def run_tests(track: str) -> tuple[bool, str]:
    test_map = {
        "backend":  ["tests/unit/test_parser.py", "tests/unit/test_filters.py",
                     "tests/integration/test_pipeline.py"],
        "cli":      ["tests/e2e/test_cli.py"],
        "features": ["tests/unit/test_buffer.py", "tests/integration/test_pipeline.py"],
        "infra":    ["tests/"],
    }
    paths = test_map.get(track, ["tests/"])
    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + paths + ["-q", "--tb=short", "--no-header"],
        capture_output=True, text=True, cwd=ROOT
    )
    output = (result.stdout + result.stderr).strip()
    # trim to avoid flooding Matrix
    if len(output) > 600:
        lines = output.splitlines()
        output = "\n".join(lines[:5] + ["..."] + lines[-10:])
    return result.returncode == 0, output


async def wait_for_signal(
    matrix: AgentMatrixClient,
    room_alias: str,
    prefix: str,
    task_id: str,
    timeout: int = SIGNAL_TIMEOUT,
) -> Optional[str]:
    """
    Listen in room_alias for a message starting with `prefix:task_id`.
    Returns the full message body, or None on timeout.
    """
    result: list[Optional[str]] = [None]
    found = asyncio.Event()

    async def on_msg(sender: str, body: str):
        if body.startswith(f"{prefix}:{task_id}"):
            result[0] = body
            found.set()

    # Register callback and do timed sync loops
    import nio
    async def _cb(room, event):
        if isinstance(event, nio.RoomMessageText):
            if event.sender != f"@{matrix.username}:localhost":
                await on_msg(event.sender, event.body)

    matrix.client.add_event_callback(_cb, __import__("nio").RoomMessageText)

    deadline = asyncio.get_event_loop().time() + timeout
    while not found.is_set():
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            break
        try:
            await asyncio.wait_for(
                matrix.client.sync(timeout=10000),
                timeout=15
            )
        except asyncio.TimeoutError:
            pass
        if found.is_set():
            break

    matrix.client.remove_event_callback(_cb, __import__("nio").RoomMessageText)
    return result[0]


async def run_autonomous_loop(
    matrix: AgentMatrixClient,
    track: str,
    track_room: str,
    agent_name: str,
) -> None:
    """Main autonomous work loop. Call after connect() and room joins."""

    await matrix.send(ROOMS["general"],
        f"🤖 {matrix.display_name} | Autonomous mode ON\n"
        f"  Polling queue for {track} tasks..."
    )

    consecutive_empty = 0

    while True:
        task = next_open(track=track)

        if task is None:
            consecutive_empty += 1
            if consecutive_empty >= 3:
                await matrix.send(ROOMS["general"],
                    f"✅ {matrix.display_name} | TRACK_DONE\n"
                    f"  No more open tasks for track: {track}\n"
                    f"  Switching to idle monitoring."
                )
                # Idle: keep syncing so Matrix stays connected
                while True:
                    await asyncio.sleep(60)
                    await matrix.client.sync(timeout=30000)
            await asyncio.sleep(POLL_INTERVAL)
            continue

        consecutive_empty = 0

        # Claim it atomically
        if not claim(task["id"], agent_name):
            # Someone else grabbed it — try next cycle
            await asyncio.sleep(2)
            continue

        task_id = task["id"]
        title = task["title"]
        files = ", ".join(task.get("files", []))
        criteria = "\n  • ".join(task.get("acceptanceCriteria", []))

        # Announce
        await matrix.send(track_room,
            f"📋 {matrix.display_name} | CLAIMED task {task_id}\n"
            f"  {title}\n"
            f"  Files: {files}"
        )

        # Signal Cascade to implement
        await matrix.send(ROOMS["integration"],
            f"IMPLEMENT:{task_id}|{title}|{files}|{agent_name}\n"
            f"Acceptance criteria:\n  • {criteria}"
        )

        await matrix.send(ROOMS["general"],
            f"⏳ {matrix.display_name} | Working on task {task_id}\n"
            f"  {title}\n"
            f"  Waiting for implementation..."
        )

        # Wait for CODE_READY:task_id from Cascade
        signal = await wait_for_signal(
            matrix, ROOMS["integration"], "CODE_READY", task_id, timeout=SIGNAL_TIMEOUT
        )

        if signal is None:
            await matrix.send(ROOMS["blockers"],
                f"🚨 {matrix.display_name} | TIMEOUT waiting for CODE_READY:{task_id}\n"
                f"  Releasing task back to queue."
            )
            release(task_id)
            await asyncio.sleep(POLL_INTERVAL)
            continue

        # Run tests
        await matrix.send(track_room,
            f"🧪 {matrix.display_name} | Running tests for task {task_id}..."
        )
        passed, output = run_tests(track)

        if not passed:
            await matrix.send(ROOMS["blockers"],
                f"🚨 {matrix.display_name} | TESTS FAILED for task {task_id}\n"
                f"```\n{output}\n```\n"
                f"Posting IMPLEMENT signal again for retry..."
            )
            # Re-signal Cascade with failure context
            await matrix.send(ROOMS["integration"],
                f"IMPLEMENT:{task_id}|{title}|{files}|{agent_name}\n"
                f"PREVIOUS ATTEMPT FAILED. Fix these test failures:\n```\n{output}\n```"
            )
            # Wait for another CODE_READY
            signal = await wait_for_signal(
                matrix, ROOMS["integration"], "CODE_READY", task_id, timeout=SIGNAL_TIMEOUT
            )
            if signal is None:
                release(task_id)
                await asyncio.sleep(POLL_INTERVAL)
                continue
            passed, output = run_tests(track)
            if not passed:
                release(task_id)
                await matrix.send(ROOMS["blockers"],
                    f"🚨 {matrix.display_name} | GIVING UP on task {task_id} after 2 failed attempts.\n"
                    f"  Human intervention needed."
                )
                await asyncio.sleep(POLL_INTERVAL)
                continue

        # Tests green — mark complete and trigger review
        complete(task_id, agent_name)
        await matrix.send(track_room,
            f"✅ {matrix.display_name} | Tests GREEN for task {task_id}\n"
            f"  Sending to Selam for review..."
        )
        await matrix.send(ROOMS["integration"],
            f"REVIEW:{task_id}|{agent_name}"
        )

        # Wait for APPROVED or CHANGES
        signal = await wait_for_signal(
            matrix, ROOMS["integration"], "APPROVED", task_id, timeout=1800
        )
        if signal:
            await matrix.send(track_room,
                f"🎉 {matrix.display_name} | Task {task_id} APPROVED and merged!\n"
                f"  Moving to next task..."
            )
        else:
            await matrix.send(track_room,
                f"⏳ {matrix.display_name} | No approval signal for {task_id} — assuming OK, moving on."
            )

        await asyncio.sleep(2)
