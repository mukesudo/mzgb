#!/usr/bin/env python3
"""
distribute.py — sync task files from openspec/changes/logsnap/tasks.md
into track-specific files in tasks/.

Usage:
    python tasks/distribute.py          # dry-run: show what would change
    python tasks/distribute.py --apply  # write changes to track files

How it works:
    Reads tasks.md, maps each phase number to a track, and reports
    whether the checkbox state in tasks.md matches each track file.
    Use --apply to push checkbox state from tasks.md → track files
    (tasks.md is the single source of truth).
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

TASKS_MD = ROOT / "openspec/changes/logsnap/tasks.md"
TRACKS_DIR = ROOT / "tasks"

# Maps phase number → track file (basename only)
PHASE_TRACK_MAP = {
    1:  "infra.md",
    2:  "backend.md",
    3:  "backend.md",
    4:  "backend.md",
    5:  "cli.md",
    6:  "cli.md",
    7:  "features.md",
    8:  "features.md",
    9:  "features.md",
    10: "infra.md",
}

TASK_RE = re.compile(r"^- \[([ x])\] (\d+)\.(\d+) (.+)$")


def parse_tasks(path: Path) -> dict[str, dict]:
    """Parse tasks.md into {task_id: {checked, description}}."""
    tasks = {}
    for line in path.read_text().splitlines():
        m = TASK_RE.match(line.strip())
        if m:
            checked, phase, sub, desc = m.group(1), m.group(2), m.group(3), m.group(4)
            task_id = f"{phase}.{sub}"
            tasks[task_id] = {"checked": checked == "x", "description": desc, "phase": int(phase)}
    return tasks


def parse_track(path: Path) -> dict[str, bool]:
    """Parse a track file into {task_id: checked}."""
    tasks = {}
    if not path.exists():
        return tasks
    for line in path.read_text().splitlines():
        m = TASK_RE.match(line.strip())
        if m:
            checked, phase, sub = m.group(1), m.group(2), m.group(3)
            tasks[f"{phase}.{sub}"] = checked == "x"
    return tasks


def update_track(path: Path, updates: dict[str, bool]) -> None:
    """Apply checkbox updates to a track file in-place."""
    lines = path.read_text().splitlines()
    result = []
    for line in lines:
        m = TASK_RE.match(line.strip())
        if m:
            phase, sub = m.group(2), m.group(3)
            task_id = f"{phase}.{sub}"
            if task_id in updates:
                marker = "x" if updates[task_id] else " "
                line = re.sub(r"\[([ x])\]", f"[{marker}]", line, count=1)
        result.append(line)
    path.write_text("\n".join(result) + "\n")


def main():
    apply = "--apply" in sys.argv

    if not TASKS_MD.exists():
        print(f"ERROR: {TASKS_MD} not found")
        sys.exit(1)

    source_tasks = parse_tasks(TASKS_MD)
    diffs: dict[str, list[tuple[str, bool, bool]]] = {}

    for task_id, info in source_tasks.items():
        track_file = PHASE_TRACK_MAP.get(info["phase"])
        if not track_file:
            continue
        track_path = TRACKS_DIR / track_file
        track_tasks = parse_track(track_path)

        if task_id in track_tasks:
            src_checked = info["checked"]
            trk_checked = track_tasks[task_id]
            if src_checked != trk_checked:
                diffs.setdefault(track_file, []).append((task_id, trk_checked, src_checked))

    if not diffs:
        print("✅  All track files are in sync with tasks.md")
        return

    print(f"{'DRY RUN — ' if not apply else ''}Changes from tasks.md → track files:\n")
    updates_by_track: dict[str, dict[str, bool]] = {}
    for track_file, changes in diffs.items():
        print(f"  {track_file}")
        for task_id, old, new in changes:
            old_s = "[x]" if old else "[ ]"
            new_s = "[x]" if new else "[ ]"
            print(f"    {task_id}  {old_s} → {new_s}")
            updates_by_track.setdefault(track_file, {})[task_id] = new
        print()

    if apply:
        for track_file, updates in updates_by_track.items():
            update_track(TRACKS_DIR / track_file, updates)
        print("✅  Track files updated.")
    else:
        print("Run with --apply to write these changes.")


if __name__ == "__main__":
    main()
