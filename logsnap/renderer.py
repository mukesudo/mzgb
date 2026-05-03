import re
import sys
from typing import Optional

from logsnap.parser import LogLine

_RESET  = "\033[0m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_GREEN  = "\033[32m"
_CYAN   = "\033[36m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"

_LEVEL_COLORS = {
    "CRITICAL": _RED,
    "FATAL":    _RED,
    "ERROR":    _RED,
    "WARN":     _YELLOW,
    "WARNING":  _YELLOW,
    "INFO":     _GREEN,
    "DEBUG":    _CYAN,
    "TRACE":    _DIM,
}


def _use_color() -> bool:
    """Return True only when stdout is a real TTY."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _colorize(text: str, color: str) -> str:
    if not _use_color():
        return text
    return f"{color}{text}{_RESET}"


def _highlight(raw: str, pattern: Optional[re.Pattern]) -> str:
    """Bold-highlight all occurrences of pattern in raw."""
    if pattern is None or not _use_color():
        return raw
    return pattern.sub(lambda m: f"{_BOLD}{m.group(0)}{_RESET}", raw)


class Renderer:
    """Render LogLine objects to stdout."""

    def __init__(self, pattern: Optional[str] = None):
        self._pattern: Optional[re.Pattern] = None
        if pattern:
            try:
                self._pattern = re.compile(pattern, re.IGNORECASE)
            except re.error:
                pass

    def print_match(self, line: LogLine) -> None:
        """Print a single matched line with color-coded level and highlighted match."""
        color = _LEVEL_COLORS.get(line.level or "", "")
        if color and _use_color():
            level_tag = _colorize(f"[{line.level}]", color)
            rest = _highlight(line.raw, self._pattern)
            print(f"{level_tag} {rest}")
        else:
            print(_highlight(line.raw, self._pattern))

    def print_separator(self) -> None:
        """Print a --- separator between non-adjacent context groups."""
        print(_colorize("--", _DIM))
