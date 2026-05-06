"""CLI entry point for mzgb — log filtering by level, pattern, and time range."""
import bz2
import glob as glob_module
import gzip
import os
import sys
import time
from datetime import datetime
from typing import Any, Generator, Iterator, List, Optional, Tuple

import click
from rich.console import Console
from rich.text import Text

from mzgb import __version__
from mzgb.buffer import context_window
from mzgb.filters import FilterPipeline, LevelFilter, PatternFilter, TimeRangeFilter
from mzgb.follow import follow_file
from mzgb.parser import detect_format, parse_line
from mzgb.renderer import Renderer
from mzgb.summary import print_summary, summarize_with_progress

_console = Console(stderr=True, highlight=False)


def _print_banner() -> None:
    """Print the full mzgb banner (used in help context)."""
    c = Console(stderr=True, highlight=False, force_terminal=True)
    c.print()
    c.print("""                                     █████    
                                    ▒▒███     
 █████████████    █████████  ███████ ▒███████ 
▒▒███▒▒███▒▒███  ▒█▒▒▒▒███  ███▒▒███ ▒███▒▒███
 ▒███ ▒███ ▒███  ▒   ███▒  ▒███ ▒███ ▒███ ▒███
 ▒███ ▒███ ▒███    ███▒   █▒███ ▒███ ▒███ ▒███
 █████▒███ █████  █████████▒▒███████ ████████ 
▒▒▒▒▒ ▒▒▒ ▒▒▒▒▒  ▒▒▒▒▒▒▒▒▒  ▒▒▒▒▒███▒▒▒▒▒▒▒▒  
                            ███ ▒███          
                           ▒▒██████           
                            ▒▒▒▒▒▒            """)
    t = Text()
    t.append("⚡ ", style="bold yellow")
    t.append("mz", style="bold white")
    t.append("gb", style="bold cyan")
    t.append(f"  v{__version__}", style="dim")
    t.append("  ·  MIT  ·  Python 3.9+", style="dim")
    c.print(t)
    c.print("  Fast log filtering by level, pattern, and time range.", style="dim")
    c.print()


def _print_status(msg: str) -> None:
    """Print a one-line status hint to stderr (only on a TTY)."""
    if _console.is_terminal:
        status = Text()
        status.append("⚡ ", style="bold yellow")
        status.append("mzgb ", style="bold cyan")
        status.append(f"v{__version__}  ", style="dim")
        status.append(msg, style="dim")
        _console.print(status)


def stream_lines(path: Optional[str]) -> Generator[str, None, None]:
    """Yield lines one at a time from a file path or stdin.

    Args:
        path: File path to read. Pass '-' to read from stdin.
              Pass an empty value to default to stdin.
              Transparently handles .gz files.

    Yields:
        Each line as a string with the trailing newline stripped.
    """
    if path is None or path == "-":
        for line in sys.stdin:
            yield line.rstrip("\n")
        return

    if path.endswith(".gz"):
        open_fn = gzip.open
    elif path.endswith(".bz2"):
        open_fn = bz2.open
    else:
        open_fn = open
    with open_fn(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            yield line.rstrip("\n")


def stream_files(files: tuple) -> Generator[Tuple[str, int, str], None, None]:
    """Yield (filename, lineno, raw) for each line across all files.

    Falls back to stdin when files is empty. Expands glob patterns on all platforms.

    Yields:
        (filename, 1-based line number, raw line text)
    """
    if not files:
        for lineno, line in enumerate(sys.stdin, 1):
            yield ("-", lineno, line.rstrip("\n"))
        return
    for fname in files:
        for lineno, raw in enumerate(stream_lines(fname), 1):
            yield (fname, lineno, raw)


def _help_callback(ctx: click.Context, _param: Any, value: bool) -> None:
    """Eager callback that prints the banner then the help text."""
    if not value or ctx.resilient_parsing:
        return
    _print_banner()
    click.echo(ctx.get_help())
    ctx.exit()


def _version_callback(ctx: click.Context, _param: Any, value: bool) -> None:
    """Eager callback that prints the version and exits."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"mzgb v{__version__}")
    ctx.exit()


def _parse_time_range(
    from_dt: Optional[str],
    to_dt: Optional[str],
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Parse --from / --to strings into datetime objects."""
    from mzgb.parser import normalize_timestamp
    from_dt_parsed: Optional[datetime] = None
    to_dt_parsed: Optional[datetime] = None
    if from_dt:
        from_dt_parsed = normalize_timestamp(from_dt)
        if from_dt_parsed is None:
            raise click.BadParameter(f"Cannot parse date: {from_dt!r}", param_hint="'--from'")
    if to_dt:
        to_dt_parsed = normalize_timestamp(to_dt)
        if to_dt_parsed is None:
            raise click.BadParameter(f"Cannot parse date: {to_dt!r}", param_hint="'--to'")
    return from_dt_parsed, to_dt_parsed


def _build_pipeline(
    level: tuple,
    pattern: Optional[str],
    from_dt_parsed: Optional[datetime],
    to_dt_parsed: Optional[datetime],
) -> FilterPipeline:
    """Build a FilterPipeline from CLI option values."""
    filters: list = []
    if level:
        filters.append(LevelFilter(list(level)))
    if pattern:
        filters.append(PatternFilter(pattern))
    if from_dt_parsed or to_dt_parsed:
        filters.append(TimeRangeFilter(from_dt_parsed, to_dt_parsed))
    return FilterPipeline(filters)


def _peek_and_detect(stream) -> Tuple[List[Tuple], str]:
    """Peek first 20 items from (fname, lineno, raw) stream and detect log format."""
    buf: List[Tuple] = []
    for item in stream:
        buf.append(item)
        if len(buf) >= 20:
            break
    raws = [item[2] for item in buf]
    return buf, detect_format(raws)


def _run_follow(file: str, pipeline: FilterPipeline, renderer: Renderer) -> None:
    """Stream new lines from a file as they arrive (tail -f mode)."""
    for raw in follow_file(file):
        parsed = parse_line(raw, "plaintext")
        if pipeline.match(parsed):
            renderer.print_match(parsed)


def _emit(renderer: Renderer, parsed, output: str, lineno: Optional[int], filename: Optional[str]) -> None:
    """Emit a single matched line in the requested output format."""
    if output == "json":
        renderer.print_json(parsed, lineno, filename)
    elif output == "csv":
        renderer.print_csv_row(parsed, lineno, filename)
    else:
        renderer.print_match(parsed, lineno, filename)


def _run_filter(
    pipeline: FilterPipeline,
    renderer: Renderer,
    stream,
    fmt: str,
    invert: bool = False,
    output: str = "text",
    show_filename: bool = False,
    show_lineno: bool = False,
) -> None:
    """Stream (fname, lineno, raw) triples through the filter pipeline and print matches."""
    use_live = sys.stderr.isatty()
    started = time.monotonic()
    scanned = 0
    matched = 0
    live = None
    if use_live:
        from rich.live import Live
        live = Live("", console=_console, refresh_per_second=15, transient=True)
        live.start()
    try:
        for fname, lineno, raw in stream:
            scanned += 1
            parsed = parse_line(raw, fmt)
            is_match = pipeline.match(parsed)
            if invert:
                is_match = not is_match
            if is_match:
                matched += 1
                _emit(
                    renderer, parsed, output,
                    lineno if show_lineno else None,
                    fname if show_filename else None,
                )
            if use_live and live and scanned % 1000 == 0:
                elapsed = time.monotonic() - started
                rate = int(scanned / elapsed) if elapsed > 0 else 0
                live.update(
                    f"⠋ scanning {scanned:,} lines ({rate:,}/s)  ✓ {matched:,} matches"
                )
    finally:
        if live:
            live.stop()
    elapsed = time.monotonic() - started
    rate = int(scanned / elapsed) if elapsed > 0 else 0
    if use_live:
        _console.print(f"✓ scanned {scanned:,} lines in {elapsed:.2f}s ({rate:,}/s)  matched {matched:,}")


def _run_context(
    pipeline: FilterPipeline,
    renderer: Renderer,
    stream,
    fmt: str,
    ctx_size: int,
    invert: bool = False,
    output: str = "text",
) -> None:
    """Stream lines through context-window mode and print with separators."""
    raw_iter = (raw for _, _, raw in stream)
    pairs = ((raw, parse_line(raw, fmt)) for raw in raw_iter)
    for line, is_sep in context_window(pairs, pipeline, ctx_size, invert=invert):
        if is_sep:
            renderer.print_separator()
        elif line is not None:
            _emit(renderer, line, output, None, None)


@click.command(
    context_settings=dict(max_content_width=100),
    add_help_option=False,
)
@click.pass_context
@click.argument("files", nargs=-1, type=click.Path())
@click.option("--help", "-h", is_flag=True, is_eager=True, expose_value=False,
              callback=_help_callback, help="Show this message and exit.")
@click.option("--version", "-V", is_flag=True, is_eager=True, expose_value=False,
              callback=_version_callback, help="Show the version and exit.")
@click.option("--level", "-l", multiple=True, help="Filter by log level (e.g. ERROR, WARN). Repeatable.")
@click.option("--pattern", "-p", default=None, help="Filter by keyword or regex pattern.")
@click.option("--from", "from_dt", default=None, help="Start of time range (e.g. '2024-01-15 14:00:00').")
@click.option("--to", "to_dt", default=None, help="End of time range.")
@click.option("--context", "-C", default=0, type=int, help="Show N lines before and after each match.")
@click.option("--follow", "-f", is_flag=True, help="Follow file for new lines (like tail -f).")
@click.option("--summary", "-s", is_flag=True, help="Show summary table instead of raw lines.")
@click.option("--invert", "-v", is_flag=True, help="Print lines that do NOT match.")
@click.option("--line-numbers", "-n", is_flag=True, help="Show source line numbers.")
@click.option("--no-color", is_flag=True, help="Disable colored output.")
@click.option("--output", "-o", default="text",
              type=click.Choice(["text", "json", "csv"], case_sensitive=False),
              help="Output format: text (default), json (NDJSON), or csv.")
def main(  # noqa: PLR0913
    ctx: click.Context,
    files: tuple,
    level: tuple,
    pattern: Optional[str],
    from_dt: Optional[str],
    to_dt: Optional[str],
    context: int,
    follow: bool,
    summary: bool,
    invert: bool,
    line_numbers: bool,
    no_color: bool,
    output: str,
) -> None:
    """mzgb — smart filter for very large log files.

    \b
    Examples:
      mzgb --level ERROR app.log
      mzgb --pattern "timeout" --context 3 app.log
      mzgb --from "2024-01-15 14:00" --to "2024-01-15 15:00" app.log
      mzgb --summary app.log
      mzgb --follow --level ERROR app.log
      cat app.log | mzgb --pattern "connection refused"
      mzgb --invert --level DEBUG app.log
      mzgb --output json --level ERROR *.log
    """
    # Expand globs and validate file existence
    all_files: List[str] = []
    for pat in files:
        matches = glob_module.glob(pat)
        all_files.extend(sorted(matches) if matches else [pat])

    for f in all_files:
        if not os.path.exists(f):
            raise click.UsageError(f"Path does not exist: {f!r}")

    _print_status(f"reading {all_files[0]!r}" if all_files else "reading from stdin")

    if not all_files and sys.stdin.isatty():
        raise click.UsageError("Provide a FILE argument or pipe input via stdin.")

    from_dt_parsed, to_dt_parsed = _parse_time_range(from_dt, to_dt)
    pipeline = _build_pipeline(level, pattern, from_dt_parsed, to_dt_parsed)
    show_filename = len(all_files) > 1
    renderer = Renderer(
        pattern=pattern,
        no_color=no_color,
        show_filename=show_filename,
        show_lineno=line_numbers,
    )

    # Follow mode — single file only
    if follow:
        if len(all_files) != 1:
            raise click.UsageError("--follow requires exactly one FILE argument.")
        _run_follow(all_files[0], pipeline, renderer)
        return

    # Build combined stream
    file_stream = stream_files(tuple(all_files))
    peeked_buf, fmt = _peek_and_detect(file_stream)

    def process_all() -> Generator[Tuple[str, int, str], None, None]:
        """Yield peeked lines then remaining stream."""
        yield from peeked_buf
        yield from file_stream

    # Summary mode
    if summary:
        parsed_lines = (parse_line(raw, fmt) for _, _, raw in process_all())
        print_summary(summarize_with_progress(parsed_lines))
        return

    # Context mode
    if context > 0:
        _run_context(pipeline, renderer, process_all(), fmt, context, invert=invert, output=output)
        return

    # Default: stream and filter
    _run_filter(
        pipeline, renderer, process_all(), fmt,
        invert=invert, output=output,
        show_filename=show_filename, show_lineno=line_numbers,
    )
