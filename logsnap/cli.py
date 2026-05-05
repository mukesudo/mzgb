import gzip
import sys
from datetime import datetime
from typing import Generator, List, Optional

import click

from logsnap.buffer import context_window
from logsnap.filters import FilterPipeline, LevelFilter, PatternFilter, TimeRangeFilter
from logsnap.follow import follow_file
from logsnap.parser import detect_format, parse_line
from logsnap.renderer import Renderer
from logsnap.summary import print_summary, summarize


def stream_lines(path: Optional[str]) -> Generator[str, None, None]:
    """Yield lines one at a time from a file path or stdin.

    Args:
        path: File path, '-' for stdin, or None for stdin.
              Transparently handles .gz files.

    Yields:
        Each line as a string with the trailing newline stripped.
    """
    if path is None or path == "-":
        for line in sys.stdin:
            yield line.rstrip("\n")
        return

    open_fn = gzip.open if path.endswith(".gz") else open
    with open_fn(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            yield line.rstrip("\n")


@click.command()
@click.argument("file", type=click.Path(exists=True), required=False)
@click.option("--level", "-l", multiple=True, help="Filter by log level (e.g. ERROR, WARN). Repeatable.")
@click.option("--pattern", "-p", default=None, help="Filter by keyword or regex pattern.")
@click.option("--from", "from_dt", default=None, help="Start of time range (e.g. '2024-01-15 14:00:00').")
@click.option("--to", "to_dt", default=None, help="End of time range.")
@click.option("--context", "-C", default=0, type=int, help="Show N lines before and after each match.")
@click.option("--follow", "-f", is_flag=True, help="Follow file for new lines (like tail -f).")
@click.option("--summary", "-s", is_flag=True, help="Show summary table instead of raw lines.")
def main(file, level, pattern, from_dt, to_dt, context, follow, summary):
    """LogSnap — smart filter for very large log files.

    \b
    Examples:
      logsnap --level ERROR app.log
      logsnap --pattern "timeout" --context 3 app.log
      logsnap --from "2024-01-15 14:00" --to "2024-01-15 15:00" app.log
      logsnap --summary app.log
      logsnap --follow --level ERROR app.log
      cat app.log | logsnap --pattern "connection refused"
    """
    if file is None and not click.get_text_stream("stdin").readable():
        raise click.UsageError("Provide a FILE argument or pipe input via stdin.")

    # Parse time range options
    from_dt_parsed: Optional[datetime] = None
    to_dt_parsed: Optional[datetime] = None
    if from_dt:
        from logsnap.parser import normalize_timestamp
        from_dt_parsed = normalize_timestamp(from_dt)
        if from_dt_parsed is None:
            raise click.BadParameter(f"Cannot parse date: {from_dt!r}", param_hint="'--from'")
    if to_dt:
        from logsnap.parser import normalize_timestamp
        to_dt_parsed = normalize_timestamp(to_dt)
        if to_dt_parsed is None:
            raise click.BadParameter(f"Cannot parse date: {to_dt!r}", param_hint="'--to'")

    # Build filter pipeline
    filters: list = []
    if level:
        filters.append(LevelFilter(list(level)))
    if pattern:
        filters.append(PatternFilter(pattern))
    if from_dt_parsed or to_dt_parsed:
        filters.append(TimeRangeFilter(from_dt_parsed, to_dt_parsed))
    pipeline = FilterPipeline(filters)
    renderer = Renderer(pattern=pattern)

    # Follow mode — stream new lines as they arrive (file only)
    if follow:
        if file is None:
            raise click.UsageError("--follow requires a FILE argument.")
        raw_stream = follow_file(file)
        fmt = "plaintext"
        for raw in raw_stream:
            parsed = parse_line(raw, fmt)
            if pipeline.match(parsed):
                renderer.print_match(parsed)
        return

    # Normal mode — read file or stdin
    lines_buf: List[str] = []
    raw_stream = stream_lines(file)

    # Peek first 20 lines to detect format
    for raw in raw_stream:
        lines_buf.append(raw)
        if len(lines_buf) >= 20:
            break

    fmt = detect_format(lines_buf)

    def process_all():
        for raw in lines_buf:
            yield raw
        for raw in raw_stream:
            yield raw

    # Summary mode
    if summary:
        parsed_lines = (parse_line(raw, fmt) for raw in process_all())
        print_summary(summarize(parsed_lines))
        return

    # Context mode
    if context > 0:
        pairs = ((raw, parse_line(raw, fmt)) for raw in process_all())
        for line, is_sep in context_window(pairs, pipeline, context):
            if is_sep:
                renderer.print_separator()
            else:
                renderer.print_match(line)
        return

    # Default: stream and filter
    for raw in process_all():
        parsed = parse_line(raw, fmt)
        if pipeline.match(parsed):
            renderer.print_match(parsed)
