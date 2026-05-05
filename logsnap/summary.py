import sys
import time
from collections import Counter
from typing import Iterable, Optional

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from logsnap.parser import LogLine

# Update the live display at most this often to avoid overhead on huge files.
_LIVE_REFRESH_INTERVAL_SECONDS = 0.1


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


_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def _progress_panel(frame: str, total: int, by_level: Counter, elapsed: float) -> Text:
    """Build a one-line progress indicator for the Live display."""
    rate = int(total / elapsed) if elapsed > 0 else 0
    t = Text()
    t.append(f"{frame} ", style="bold yellow")
    t.append("scanning ", style="bold cyan")
    t.append(f"{total:>10,} lines  ", style="white")
    t.append(f"({rate:>8,}/s)  ", style="dim")
    err = by_level.get("ERROR", 0) + by_level.get("FATAL", 0) + by_level.get("CRITICAL", 0)
    warn = by_level.get("WARN", 0) + by_level.get("WARNING", 0)
    if err:
        t.append(f"⛔ {err:,}  ", style="bold red")
    if warn:
        t.append(f"⚠ {warn:,}  ", style="bold yellow")
    return t


def summarize_with_progress(lines: Iterable[LogLine]) -> dict:
    """Like summarize(), but shows a live progress indicator on stderr.

    Falls back to plain summarize() when stderr is not a TTY.
    """
    if not sys.stderr.isatty():
        return summarize(lines)

    total = 0
    by_level: Counter = Counter()
    first_ts = None
    last_ts = None
    unparsed = 0

    console = Console(stderr=True, highlight=False)
    started = time.monotonic()
    last_update = 0.0
    frame_idx = 0

    with Live(
        _progress_panel(_SPINNER_FRAMES[0], 0, by_level, 0.0),
        console=console,
        refresh_per_second=15,
        transient=True,
    ) as live:
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

            now = time.monotonic()
            if now - last_update >= _LIVE_REFRESH_INTERVAL_SECONDS:
                last_update = now
                frame_idx = (frame_idx + 1) % len(_SPINNER_FRAMES)
                live.update(_progress_panel(
                    _SPINNER_FRAMES[frame_idx], total, by_level, now - started,
                ))

    elapsed = time.monotonic() - started
    rate = int(total / elapsed) if elapsed > 0 else 0
    done = Text()
    done.append("✓ ", style="bold green")
    done.append(f"scanned {total:,} lines in {elapsed:.2f}s  ", style="white")
    done.append(f"({rate:,}/s)", style="dim")
    console.print(done)

    return {
        "total": total,
        "by_level": by_level,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "unparsed": unparsed,
    }
