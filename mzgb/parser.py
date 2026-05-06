import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class LogLine:
    """A single parsed log line."""
    raw: str
    level: Optional[str] = None
    timestamp: Optional[datetime] = None
    message: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)
    cluster_id: int = -1
    template: Optional[str] = None


_TS_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%d/%b/%Y:%H:%M:%S %z",
]

_LEVEL_PLAINTEXT_RE = re.compile(
    r"\b(CRITICAL|FATAL|ERROR|WARN(?:ING)?|INFO|DEBUG|TRACE)\b",
    re.IGNORECASE,
)
_TS_PLAINTEXT_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
)


def normalize_timestamp(raw_ts: str) -> Optional[datetime]:
    """Parse a timestamp string into a datetime. Returns None on failure."""
    raw_ts = raw_ts.strip().replace(",", ".")
    for fmt in _TS_FORMATS:
        try:
            return datetime.strptime(raw_ts, fmt)
        except ValueError:
            continue
    return None


def parse_json_line(line: str) -> LogLine:
    """Parse a JSON log line into a LogLine."""
    try:
        obj = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return LogLine(raw=line)

    level = (
        obj.get("level") or obj.get("severity") or obj.get("lvl") or obj.get("LEVEL")
    )
    if level:
        level = str(level).upper()

    raw_ts = (
        obj.get("time") or obj.get("timestamp") or
        obj.get("ts") or obj.get("@timestamp")
    )
    ts = normalize_timestamp(str(raw_ts)) if raw_ts else None

    msg = obj.get("msg") or obj.get("message") or obj.get("MESSAGE") or ""

    skip = {"level", "severity", "lvl", "LEVEL",
            "time", "timestamp", "ts", "@timestamp",
            "msg", "message", "MESSAGE"}
    extras = {k: v for k, v in obj.items() if k not in skip}
    return LogLine(raw=line, level=level, timestamp=ts, message=str(msg), extras=extras)


def parse_logfmt_line(line: str) -> LogLine:
    """Parse a logfmt key=value line into a LogLine."""
    pairs: Dict[str, str] = {}
    pos = 0
    while pos < len(line):
        while pos < len(line) and line[pos] == " ":
            pos += 1
        if pos >= len(line):
            break
        eq = line.find("=", pos)
        if eq == -1:
            break
        key = line[pos:eq]
        pos = eq + 1
        if pos < len(line) and line[pos] == '"':
            end = line.find('"', pos + 1)
            if end == -1:
                value = line[pos + 1:]
                pos = len(line)
            else:
                value = line[pos + 1:end]
                pos = end + 1
        else:
            space = line.find(" ", pos)
            if space == -1:
                value = line[pos:]
                pos = len(line)
            else:
                value = line[pos:space]
                pos = space
        pairs[key] = value

    level = pairs.get("level") or pairs.get("lvl") or pairs.get("severity")
    if level:
        level = level.upper()
    raw_ts = pairs.get("time") or pairs.get("ts") or pairs.get("timestamp")
    ts = normalize_timestamp(raw_ts) if raw_ts else None
    msg = pairs.get("msg") or pairs.get("message") or ""
    skip = {"level", "lvl", "severity", "time", "ts", "timestamp", "msg", "message"}
    extras = {k: v for k, v in pairs.items() if k not in skip}
    return LogLine(raw=line, level=level, timestamp=ts, message=msg, extras=extras)


def parse_plaintext_line(line: str) -> LogLine:
    """Extract level and message from a plain-text log line."""
    level_match = _LEVEL_PLAINTEXT_RE.search(line)
    level = level_match.group(1).upper() if level_match else None
    if level == "WARNING":
        level = "WARN"

    ts_match = _TS_PLAINTEXT_RE.search(line)
    ts = normalize_timestamp(ts_match.group(1)) if ts_match else None

    if level_match:
        after = line[level_match.end():].lstrip(" :-|")
        message = after if after else line
    else:
        message = line

    return LogLine(raw=line, level=level, timestamp=ts, message=message)


def detect_format(lines: List[str]) -> str:
    """Sample up to 20 lines and return 'json', 'logfmt', or 'plaintext'."""
    sample = [l.strip() for l in lines[:20] if l.strip()]
    if not sample:
        return "plaintext"

    json_hits = 0
    logfmt_hits = 0

    for line in sample:
        if line.startswith("{"):
            try:
                json.loads(line)
                json_hits += 1
                continue
            except (json.JSONDecodeError, ValueError):
                pass
        if "=" in line and not line.startswith("{"):
            logfmt_hits += 1

    total = len(sample)
    if json_hits / total >= 0.5:
        return "json"
    if logfmt_hits / total >= 0.5:
        return "logfmt"
    return "plaintext"


def parse_line(line: str, fmt: str) -> LogLine:
    """Dispatch to the correct parser based on detected format."""
    if fmt == "json":
        return parse_json_line(line)
    if fmt == "logfmt":
        return parse_logfmt_line(line)
    return parse_plaintext_line(line)


def cluster_line(log: LogLine) -> LogLine:
    """Enrich a LogLine with drain3 cluster_id and template (in-place mutation).

    Uses the message field if available, otherwise falls back to raw.
    No-op when drain3 is not installed (cluster_id stays -1).
    """
    from mzgb.drain import cluster
    text = log.message if log.message else log.raw
    log.cluster_id, log.template = cluster(text)
    return log
