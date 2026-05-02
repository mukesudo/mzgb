"""
queue_manager.py — Atomic claim/release/complete for QUEUE.json.
Agents call this to safely pick work without stepping on each other.
"""

import json
import fcntl
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

QUEUE_PATH = Path(__file__).parent / "QUEUE.json"


def _load() -> dict:
    return json.loads(QUEUE_PATH.read_text())


def _save(data: dict) -> None:
    QUEUE_PATH.write_text(json.dumps(data, indent=2) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def next_open(track: str = None, phase: int = None) -> Optional[dict]:
    """Return the highest-priority OPEN task for a track, respecting dependencies."""
    data = _load()
    done_ids = {t["id"] for t in data["tasks"] if t["status"] in ("DONE", "MERGED")}
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

    candidates = [
        t for t in data["tasks"]
        if t["status"] == "OPEN"
        and (track is None or t.get("track") == track)
        and (phase is None or t.get("phase") == phase)
        and all(dep in done_ids for dep in t.get("dependsOn", []))
    ]
    candidates.sort(key=lambda t: (priority_order.get(t["priority"], 9), t["id"]))
    return candidates[0] if candidates else None


def claim(task_id: str, agent_name: str) -> bool:
    """Atomically claim a task. Returns True if claim succeeded."""
    with open(QUEUE_PATH, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        data = json.load(f)
        for task in data["tasks"]:
            if task["id"] == task_id:
                if task["status"] != "OPEN":
                    fcntl.flock(f, fcntl.LOCK_UN)
                    return False
                task["status"] = "CLAIMED"
                task["claimedBy"] = agent_name
                task["claimedAt"] = _now()
                task["assignedAgent"] = agent_name
                f.seek(0)
                json.dump(data, f, indent=2)
                f.write("\n")
                f.truncate()
                fcntl.flock(f, fcntl.LOCK_UN)
                return True
        fcntl.flock(f, fcntl.LOCK_UN)
    return False


def complete(task_id: str, agent_name: str) -> None:
    """Mark a task as DONE (pending review)."""
    with open(QUEUE_PATH, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        data = json.load(f)
        for task in data["tasks"]:
            if task["id"] == task_id and task.get("claimedBy") == agent_name:
                task["status"] = "REVIEW"
                task["completedAt"] = _now()
                break
        f.seek(0)
        json.dump(data, f, indent=2)
        f.write("\n")
        f.truncate()
        fcntl.flock(f, fcntl.LOCK_UN)


def approve(task_id: str) -> None:
    """Mark a task as DONE (called by Selam after review)."""
    with open(QUEUE_PATH, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        data = json.load(f)
        for task in data["tasks"]:
            if task["id"] == task_id:
                task["status"] = "DONE"
                task["approvedAt"] = _now()
                break
        f.seek(0)
        json.dump(data, f, indent=2)
        f.write("\n")
        f.truncate()
        fcntl.flock(f, fcntl.LOCK_UN)


def release(task_id: str) -> None:
    """Release a claimed task back to OPEN (e.g. on blocker)."""
    with open(QUEUE_PATH, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        data = json.load(f)
        for task in data["tasks"]:
            if task["id"] == task_id:
                task["status"] = "OPEN"
                task["claimedBy"] = None
                task["claimedAt"] = None
                break
        f.seek(0)
        json.dump(data, f, indent=2)
        f.write("\n")
        f.truncate()
        fcntl.flock(f, fcntl.LOCK_UN)


def stats() -> dict:
    """Return summary counts by status."""
    data = _load()
    counts: dict = {}
    for t in data["tasks"]:
        counts[t["status"]] = counts.get(t["status"], 0) + 1
    return counts


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if cmd == "stats":
        print(json.dumps(stats(), indent=2))
    elif cmd == "next" and len(sys.argv) > 2:
        t = next_open(track=sys.argv[2])
        print(json.dumps(t, indent=2) if t else "No open tasks")
    elif cmd == "claim" and len(sys.argv) == 4:
        print("claimed" if claim(sys.argv[2], sys.argv[3]) else "failed")
    elif cmd == "complete" and len(sys.argv) == 4:
        complete(sys.argv[2], sys.argv[3])
        print(f"{sys.argv[2]} → REVIEW")
    elif cmd == "approve" and len(sys.argv) == 3:
        approve(sys.argv[2])
        print(f"{sys.argv[2]} → DONE")
