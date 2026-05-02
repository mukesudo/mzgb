"""
Parses task markdown files into structured task objects.
Agents use this to know what to work on next and to check off completed tasks.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

TASK_RE = re.compile(r"^- \[([ x])\] (\d+)\.(\d+) (.+)$")
PHASE_RE = re.compile(r"^## Phase (\d+)")


@dataclass
class Task:
    id: str           # e.g. "2.1"
    phase: int
    description: str
    done: bool
    line_number: int


def load_tasks(task_file: Path) -> list[Task]:
    """Parse a track task file and return all tasks in order."""
    tasks = []
    current_phase = 0
    for i, line in enumerate(task_file.read_text().splitlines()):
        phase_match = PHASE_RE.match(line.strip())
        if phase_match:
            current_phase = int(phase_match.group(1))
            continue
        task_match = TASK_RE.match(line.strip())
        if task_match:
            checked, phase_num, sub, desc = task_match.groups()
            tasks.append(Task(
                id=f"{phase_num}.{sub}",
                phase=int(phase_num),
                description=desc,
                done=(checked == "x"),
                line_number=i,
            ))
    return tasks


def next_task(task_file: Path) -> Optional[Task]:
    """Return the first uncompleted task in the track file."""
    for task in load_tasks(task_file):
        if not task.done:
            return task
    return None


def mark_done(task_file: Path, task_id: str) -> None:
    """Check off a task by ID in the task file."""
    lines = task_file.read_text().splitlines()
    result = []
    for line in lines:
        m = TASK_RE.match(line.strip())
        if m:
            _, phase, sub, _ = m.groups()
            if f"{phase}.{sub}" == task_id:
                line = line.replace("- [ ]", "- [x]", 1)
        result.append(line)
    task_file.write_text("\n".join(result) + "\n")


def summary(task_file: Path) -> dict:
    """Return {total, done, pending} counts for a track file."""
    tasks = load_tasks(task_file)
    done = sum(1 for t in tasks if t.done)
    return {"total": len(tasks), "done": done, "pending": len(tasks) - done}
