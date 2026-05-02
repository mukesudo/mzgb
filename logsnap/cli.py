import gzip
import sys
from typing import Generator, Optional

import click


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

    for line in stream_lines(file):
        click.echo(line)
