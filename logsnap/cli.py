"""CLI entry point for logsnap — log filtering by level, pattern, and time range."""
import gzip
import sys
from datetime import datetime
from typing import Any, Generator, Iterator, List, Optional, Tuple

import click
from rich.console import Console
from rich.text import Text

from logsnap import __version__
from logsnap.buffer import context_window
from logsnap.filters import FilterPipeline, LevelFilter, PatternFilter, TimeRangeFilter
from logsnap.follow import follow_file
from logsnap.parser import detect_format, parse_line
from logsnap.renderer import Renderer
from logsnap.summary import print_summary, summarize_with_progress

_console = Console(stderr=True, highlight=False)


def _print_banner() -> None:
    """Print the full logsnap banner (used in help context)."""
    c = Console(stderr=True, highlight=False, force_terminal=True)
    c.print()
    c.print("""
 ████                                                          
▒▒███                                                          
 ▒███   ██████   ███████  █████  ████████    ██████   ████████ 
 ▒███  ███▒▒███ ███▒▒███ ███▒▒  ▒▒███▒▒███  ▒▒▒▒▒███ ▒▒███▒▒███
 ▒███ ▒███ ▒███▒███ ▒███▒▒█████  ▒███ ▒███   ███████  ▒███ ▒███
 ▒███ ▒███ ▒███▒███ ▒███ ▒▒▒▒███ ▒███ ▒███  ███▒▒███  ▒███ ▒███
 █████▒▒██████ ▒▒███████ ██████  ████ █████▒▒████████ ▒███████ 
▒▒▒▒▒  ▒▒▒▒▒▒   ▒▒▒▒▒███▒▒▒▒▒▒  ▒▒▒▒ ▒▒▒▒▒  ▒▒▒▒▒▒▒▒  ▒███▒▒▒  
                ███ ▒███                              ▒███     
               ▒▒██████                               █████    
                ▒▒▒▒▒▒                               ▒▒▒▒▒     """)
    t = Text()
    t.append("⚡ ", style="bold yellow")
    t.append("log", style="bold white")
    t.append("snap", style="bold cyan")
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
        status.append("logsnap ", style="bold cyan")
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
    else:
        open_fn = open
    with open_fn(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            yield line.rstrip("\n")


def _help_callback(ctx: click.Context, _param: Any, value: bool) -> None:
    """Eager callback that prints the banner then the help text."""
    if not value or ctx.resilient_parsing:
        return
    _print_banner()
    click.echo(ctx.get_help())
    ctx.exit()


def _parse_time_range(
    from_dt: Optional[str],
    to_dt: Optional[str],
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Parse --from / --to strings into datetime objects."""
    from logsnap.parser import normalize_timestamp
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


def _peek_and_detect(raw_stream: Iterator[str]) -> Tuple[List[str], str]:
    """Peek first 20 lines and detect log format."""
    lines_buf: List[str] = []
    for raw in raw_stream:
        lines_buf.append(raw)
        if len(lines_buf) >= 20:
            break
    return lines_buf, detect_format(lines_buf)


def _run_follow(file: str, pipeline: FilterPipeline, renderer: Renderer) -> None:
    """Stream new lines from a file as they arrive (tail -f mode)."""
    for raw in follow_file(file):
        parsed = parse_line(raw, "plaintext")
        if pipeline.match(parsed):
            renderer.print_match(parsed)


def _run_filter(
    pipeline: FilterPipeline,
    renderer: Renderer,
    lines: Iterator[str],
    fmt: str,
) -> None:
    """Stream lines through the filter pipeline and print matches."""
    for raw in lines:
        parsed = parse_line(raw, fmt)
        if pipeline.match(parsed):
            renderer.print_match(parsed)


def _run_context(
    pipeline: FilterPipeline,
    renderer: Renderer,
    lines: Iterator[str],
    fmt: str,
    ctx_size: int,
) -> None:
    """Stream lines through context-window mode and print with separators."""
    pairs = ((raw, parse_line(raw, fmt)) for raw in lines)
    for line, is_sep in context_window(pairs, pipeline, ctx_size):
        if is_sep:
            renderer.print_separator()
        else:
            renderer.print_match(line)


@click.command(
    context_settings=dict(max_content_width=100),
    add_help_option=False,
)
@click.pass_context
@click.argument("file", type=click.Path(exists=True), required=False)
@click.option("--help", "-h", is_flag=True, is_eager=True, expose_value=False,
              callback=_help_callback, help="Show this message and exit.")
@click.option("--level", "-l", multiple=True, help="Filter by log level (e.g. ERROR, WARN). Repeatable.")
@click.option("--pattern", "-p", default=None, help="Filter by keyword or regex pattern.")
@click.option("--from", "from_dt", default=None, help="Start of time range (e.g. '2024-01-15 14:00:00').")
@click.option("--to", "to_dt", default=None, help="End of time range.")
@click.option("--context", "-C", default=0, type=int, help="Show N lines before and after each match.")
@click.option("--follow", "-f", is_flag=True, help="Follow file for new lines (like tail -f).")
@click.option("--summary", "-s", is_flag=True, help="Show summary table instead of raw lines.")
def main(ctx: click.Context, file: Optional[str], level: tuple, pattern: Optional[str],  # noqa: PLR0913
         from_dt: Optional[str], to_dt: Optional[str], context: int,
         follow: bool, summary: bool) -> None:
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
    _print_status(f"reading {file!r}" if file else "reading from stdin")

    if file is None and not click.get_text_stream("stdin").readable():
        raise click.UsageError("Provide a FILE argument or pipe input via stdin.")

    from_dt_parsed, to_dt_parsed = _parse_time_range(from_dt, to_dt)
    pipeline = _build_pipeline(level, pattern, from_dt_parsed, to_dt_parsed)
    renderer = Renderer(pattern=pattern)

    # Follow mode — stream new lines as they arrive (file only)
    if follow:
        if file is None:
            raise click.UsageError("--follow requires a FILE argument.")
        _run_follow(file, pipeline, renderer)
        return

    # Normal mode — read file or stdin
    raw_stream = stream_lines(file)
    lines_buf, fmt = _peek_and_detect(raw_stream)

    def process_all() -> Generator[str, None, None]:
        """Yield buffered lines then remaining stream."""
        yield from lines_buf
        yield from raw_stream

    # Summary mode
    if summary:
        parsed_lines = (parse_line(raw, fmt) for raw in process_all())
        print_summary(summarize_with_progress(parsed_lines))
        return

    # Context mode
    if context > 0:
        _run_context(pipeline, renderer, process_all(), fmt, context)
        return

    # Default: stream and filter
    _run_filter(pipeline, renderer, process_all(), fmt)
