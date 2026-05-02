"""Shared fixtures for all test layers."""
import pytest
import textwrap


@pytest.fixture
def plaintext_log(tmp_path):
    """A small plain-text log file with mixed levels."""
    content = textwrap.dedent("""\
        2024-01-15 14:00:01 INFO  Service started
        2024-01-15 14:00:02 DEBUG Loading config from /etc/app.conf
        2024-01-15 14:00:05 WARN  Disk usage above 80%
        2024-01-15 14:00:10 ERROR Connection refused to db:5432
        2024-01-15 14:00:11 INFO  Retrying connection...
        2024-01-15 14:00:12 ERROR Connection refused to db:5432
        2024-01-15 14:00:15 FATAL Out of memory
    """)
    f = tmp_path / "app.log"
    f.write_text(content)
    return f


@pytest.fixture
def json_log(tmp_path):
    """A small JSON-per-line log file."""
    import json
    lines = [
        {"time": "2024-01-15T14:00:01Z", "level": "INFO",  "msg": "Service started"},
        {"time": "2024-01-15T14:00:02Z", "level": "DEBUG", "msg": "Loading config"},
        {"time": "2024-01-15T14:00:10Z", "level": "ERROR", "msg": "Connection refused"},
        {"time": "2024-01-15T14:00:15Z", "level": "FATAL", "msg": "Out of memory"},
    ]
    f = tmp_path / "app.jsonl"
    f.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
    return f


@pytest.fixture
def logfmt_log(tmp_path):
    """A small logfmt log file."""
    content = textwrap.dedent("""\
        time=2024-01-15T14:00:01Z level=INFO msg="Service started"
        time=2024-01-15T14:00:02Z level=DEBUG msg="Loading config"
        time=2024-01-15T14:00:10Z level=ERROR msg="Connection refused"
        time=2024-01-15T14:00:15Z level=FATAL msg="Out of memory"
    """)
    f = tmp_path / "app.logfmt"
    f.write_text(content)
    return f


@pytest.fixture
def large_log(tmp_path):
    """A log file with 10,000 lines for performance/streaming tests."""
    lines = []
    levels = ["DEBUG", "INFO", "INFO", "WARN", "ERROR"]
    for i in range(10_000):
        lvl = levels[i % len(levels)]
        lines.append(f"2024-01-15 14:00:{i % 60:02d} {lvl}  Message number {i}")
    f = tmp_path / "large.log"
    f.write_text("\n".join(lines) + "\n")
    return f
