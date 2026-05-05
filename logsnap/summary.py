from collections import Counter
from typing import Iterable, Optional

from logsnap.parser import LogLine


def summarize(lines: Iterable[LogLine]) -> dict:
    """Collect stats over a stream of LogLine objects.

    Returns a dict with:
        total       — total lines processed
        by_level    — Counter of level -> count
        first_ts    — earliest timestamp seen (or None)
        last_ts     — latest timestamp seen (or None)
        unparsed    — lines with no level detected
    """
    total = 0
    by_level: Counter = Counter()
    first_ts = None
    last_ts = None
    unparsed = 0

    for line in lines:
        total += 1
        if line.level:
            by_level[line.level] += 1
        else:
            unparsed += 1
        if line.timestamp:
            if first_ts is None or line.timestamp < first_ts:
                first_ts = line.timestamp
            if last_ts is None or line.timestamp > last_ts:
                last_ts = line.timestamp

    return {
        "total": total,
        "by_level": by_level,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "unparsed": unparsed,
    }


def print_summary(stats: dict) -> None:
    """Print a simple text summary table to stdout."""
    print(f"{'─' * 36}")
    print(f"  {'Total lines':<20} {stats['total']:>10,}")
    print(f"{'─' * 36}")

    order = ["FATAL", "CRITICAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG", "TRACE"]
    by_level = stats["by_level"]
    shown = set()
    for lvl in order:
        if lvl in by_level:
            print(f"  {lvl:<20} {by_level[lvl]:>10,}")
            shown.add(lvl)
    for lvl, cnt in sorted(by_level.items()):
        if lvl not in shown:
            print(f"  {lvl:<20} {cnt:>10,}")

    if stats["unparsed"]:
        print(f"  {'(no level)':<20} {stats['unparsed']:>10,}")

    print(f"{'─' * 36}")
    if stats["first_ts"]:
        print(f"  {'From':<20} {stats['first_ts'].strftime('%Y-%m-%d %H:%M:%S')}")
    if stats["last_ts"]:
        print(f"  {'To':<20} {stats['last_ts'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'─' * 36}")
