import csv as csv_module
import json
import re
import sys
from typing import Optional

from mzgb.parser import LogLine

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


class Renderer:
    """Render LogLine objects to stdout."""

    def __init__(
        self,
        pattern: tuple = (),
        no_color: bool = False,
        show_filename: bool = False,
        show_lineno: bool = False,
    ):
        self._no_color = no_color
        self._show_filename = show_filename
        self._show_lineno = show_lineno
        self._pattern: Optional[re.Pattern] = None
        self._csv_writer = None
        if pattern:
            try:
                combined = "|".join(f"(?:{p})" for p in pattern)
                self._pattern = re.compile(combined, re.IGNORECASE)
            except re.error:
                pass

    def _use_color(self) -> bool:
        if self._no_color:
            return False
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    def _colorize(self, text: str, color: str) -> str:
        if not self._use_color():
            return text
        return f"{color}{text}{_RESET}"

    def _highlight(self, raw: str) -> str:
        if self._pattern is None or not self._use_color():
            return raw
        return self._pattern.sub(lambda m: f"{_BOLD}{m.group(0)}{_RESET}", raw)

    def _prefix(self, lineno: Optional[int], filename: Optional[str]) -> str:
        parts = []
        if self._show_filename and filename and filename != "-":
            parts.append(self._colorize(filename, _DIM))
        if self._show_lineno and lineno is not None:
            parts.append(self._colorize(str(lineno), _DIM))
        return (":".join(parts) + ":") if parts else ""

    def print_match(self, line: LogLine, lineno: Optional[int] = None, filename: Optional[str] = None) -> None:
        """Print a single matched line with color-coded level and highlighted match."""
        prefix = self._prefix(lineno, filename)
        color = _LEVEL_COLORS.get(line.level or "", "")
        if color and self._use_color():
            level_tag = self._colorize(f"[{line.level}]", color)
            print(f"{prefix}{level_tag} {self._highlight(line.raw)}")
        else:
            print(f"{prefix}{self._highlight(line.raw)}")

    def print_json(self, line: LogLine, lineno: Optional[int] = None, filename: Optional[str] = None) -> None:
        """Emit a single matched line as a JSON object (NDJSON)."""
        obj = {
            "ts": str(line.timestamp) if line.timestamp else None,
            "level": line.level,
            "msg": line.message or line.raw,
            "file": filename if filename and filename != "-" else None,
            "lineno": lineno,
        }
        print(json.dumps(obj))

    def print_csv_row(self, line: LogLine, lineno: Optional[int] = None, filename: Optional[str] = None) -> None:
        """Emit a single matched line as a CSV row (writes header on first call)."""
        if self._csv_writer is None:
            self._csv_writer = csv_module.writer(sys.stdout)
            self._csv_writer.writerow(["ts", "level", "msg", "file", "lineno"])
        self._csv_writer.writerow([
            str(line.timestamp) if line.timestamp else "",
            line.level or "",
            line.message or line.raw,
            filename if filename and filename != "-" else "",
            lineno if lineno is not None else "",
        ])

    def print_separator(self) -> None:
        """Print a --- separator between non-adjacent context groups."""
        print(self._colorize("--", _DIM))
