"""Unit tests — summary mode including live-progress path."""
import sys
from collections import Counter
from io import StringIO

import pytest

from logsnap.parser import LogLine
from logsnap.summary import (
    _SPINNER_FRAMES,
    _progress_panel,
    print_summary,
    summarize,
    summarize_with_progress,
)


def _make(level=None, ts=None):
    return LogLine(raw="x", level=level, timestamp=ts)


class TestSummarize:
    def test_counts_total(self):
        lines = [_make("ERROR"), _make("INFO"), _make("INFO")]
        stats = summarize(lines)
        assert stats["total"] == 3

    def test_counts_by_level(self):
        lines = [_make("ERROR"), _make("INFO"), _make("ERROR")]
        stats = summarize(lines)
        assert stats["by_level"]["ERROR"] == 2
        assert stats["by_level"]["INFO"] == 1

    def test_unparsed_counted(self):
        stats = summarize([_make(None)])
        assert stats["unparsed"] == 1

    def test_timestamps_tracked(self):
        from datetime import datetime
        t1 = datetime(2024, 1, 1, 0, 0, 0)
        t2 = datetime(2024, 1, 2, 0, 0, 0)
        stats = summarize([_make(ts=t1), _make(ts=t2)])
        assert stats["first_ts"] == t1
        assert stats["last_ts"] == t2

    def test_empty_stream(self):
        stats = summarize([])
        assert stats["total"] == 0
        assert stats["first_ts"] is None
        assert stats["last_ts"] is None


class TestProgressPanel:
    def test_returns_text(self):
        from rich.text import Text
        t = _progress_panel(_SPINNER_FRAMES[0], 100, Counter({"ERROR": 5}), 1.0)
        assert isinstance(t, Text)

    def test_zero_elapsed_no_crash(self):
        t = _progress_panel(_SPINNER_FRAMES[0], 0, Counter(), 0.0)
        assert t is not None

    def test_shows_error_count(self):
        t = _progress_panel("⠋", 10, Counter({"ERROR": 3}), 1.0)
        assert "3" in t.plain

    def test_shows_warn_count(self):
        t = _progress_panel("⠋", 10, Counter({"WARN": 7}), 1.0)
        assert "7" in t.plain


class TestSummarizeWithProgress:
    def test_non_tty_falls_back_to_plain(self, monkeypatch):
        monkeypatch.setattr(sys, "stderr", StringIO())
        lines = [_make("ERROR"), _make("INFO")]
        stats = summarize_with_progress(lines)
        assert stats["total"] == 2
        assert stats["by_level"]["ERROR"] == 1

    def test_tty_path_returns_correct_stats(self, monkeypatch):
        """Force TTY path by monkeypatching isatty."""
        fake_stderr = StringIO()
        fake_stderr.isatty = lambda: True
        monkeypatch.setattr(sys, "stderr", fake_stderr)

        from datetime import datetime
        ts = datetime(2024, 1, 15, 12, 0, 0)
        lines = [
            _make("ERROR", ts=ts),
            _make("WARN"),
            _make(None),
        ]
        stats = summarize_with_progress(lines)
        assert stats["total"] == 3
        assert stats["by_level"]["ERROR"] == 1
        assert stats["unparsed"] == 1
        assert stats["first_ts"] == ts


class TestPrintSummary:
    def test_prints_total(self, capsys):
        stats = {
            "total": 42,
            "by_level": Counter({"ERROR": 5, "INFO": 37}),
            "first_ts": None,
            "last_ts": None,
            "unparsed": 0,
        }
        print_summary(stats)
        out = capsys.readouterr().out
        assert "42" in out
        assert "ERROR" in out
        assert "INFO" in out

    def test_prints_time_range(self, capsys):
        from datetime import datetime
        stats = {
            "total": 1,
            "by_level": Counter(),
            "first_ts": datetime(2024, 1, 15, 12, 0, 0),
            "last_ts": datetime(2024, 1, 15, 14, 0, 0),
            "unparsed": 0,
        }
        print_summary(stats)
        out = capsys.readouterr().out
        assert "2024-01-15" in out

    def test_prints_unparsed(self, capsys):
        stats = {
            "total": 5,
            "by_level": Counter(),
            "first_ts": None,
            "last_ts": None,
            "unparsed": 3,
        }
        print_summary(stats)
        out = capsys.readouterr().out
        assert "no level" in out
