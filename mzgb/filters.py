import re
from datetime import datetime
from typing import List, Optional

from mzgb.parser import LogLine


class LevelFilter:
    """Match a LogLine by one or more log levels (case-insensitive)."""

    def __init__(self, levels: List[str]):
        self.levels = {l.upper() for l in levels}

    def match(self, line: LogLine) -> bool:
        if not self.levels:
            return True
        return bool(line.level and line.level.upper() in self.levels)


class PatternFilter:
    """Match a LogLine by a regex pattern or plain keyword."""

    def __init__(self, pattern: str):
        try:
            self._re = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern {pattern!r}: {e}") from e

    def match(self, line: LogLine) -> bool:
        return bool(self._re.search(line.raw))


class TimeRangeFilter:
    """Match a LogLine whose timestamp falls within [from_dt, to_dt]."""

    def __init__(self, from_dt: Optional[datetime] = None, to_dt: Optional[datetime] = None):
        self.from_dt = from_dt
        self.to_dt = to_dt

    def match(self, line: LogLine) -> bool:
        if self.from_dt is None and self.to_dt is None:
            return True
        if line.timestamp is None:
            return False
        ts = line.timestamp.replace(tzinfo=None) if line.timestamp.tzinfo else line.timestamp
        if self.from_dt:
            f = self.from_dt.replace(tzinfo=None) if self.from_dt.tzinfo else self.from_dt
            if ts < f:
                return False
        if self.to_dt:
            t = self.to_dt.replace(tzinfo=None) if self.to_dt.tzinfo else self.to_dt
            if ts > t:
                return False
        return True


class FilterPipeline:
    """AND-compose multiple filters — all must pass for a line to match."""

    def __init__(self, filters: list):
        self.filters = filters

    def match(self, line: LogLine) -> bool:
        return all(f.match(line) for f in self.filters)
