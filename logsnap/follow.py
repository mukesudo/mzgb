import time
from typing import Generator


def follow_file(path: str, poll_interval: float = 0.1) -> Generator[str, None, None]:
    """Yield new lines appended to a file, like tail -f.

    Args:
        path:          Path to the file to follow.
        poll_interval: Seconds to sleep between polls when no new data.

    Yields:
        Each new line (newline stripped) as it appears.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        fh.seek(0, 2)
        while True:
            line = fh.readline()
            if line:
                yield line.rstrip("\n")
            else:
                time.sleep(poll_interval)
