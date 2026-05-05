"""Unit tests — context window (Phase 7)."""
from logsnap.buffer import context_window
from logsnap.filters import FilterPipeline, PatternFilter
from logsnap.parser import LogLine


def _make(level: str, msg: str) -> LogLine:
    return LogLine(raw=f"{level} {msg}", level=level, message=msg)


def _stream(*lines: LogLine):
    return ((l.raw, l) for l in lines)


class TestContextWindow:
    def test_no_context_returns_only_matches(self):
        lines = [_make("INFO", "a"), _make("ERROR", "boom"), _make("INFO", "b")]
        pipeline = FilterPipeline([PatternFilter("boom")])
        results = list(context_window(_stream(*lines), pipeline, 0))
        parsed = [p for p, sep in results if not sep]
        assert len(parsed) == 1
        assert parsed[0].message == "boom"

    def test_before_context(self):
        lines = [_make("INFO", "a"), _make("INFO", "b"), _make("ERROR", "boom")]
        pipeline = FilterPipeline([PatternFilter("boom")])
        results = list(context_window(_stream(*lines), pipeline, 2))
        parsed = [p for p, sep in results if not sep]
        assert len(parsed) == 3
        assert [p.message for p in parsed] == ["a", "b", "boom"]

    def test_after_context(self):
        lines = [_make("ERROR", "boom"), _make("INFO", "a"), _make("INFO", "b")]
        pipeline = FilterPipeline([PatternFilter("boom")])
        results = list(context_window(_stream(*lines), pipeline, 2))
        parsed = [p for p, sep in results if not sep]
        assert len(parsed) == 3
        assert [p.message for p in parsed] == ["boom", "a", "b"]

    def test_separator_between_non_adjacent_matches(self):
        lines = [
            _make("ERROR", "boom1"),
            _make("INFO", "a"),
            _make("INFO", "b"),
            _make("INFO", "c"),
            _make("INFO", "d"),
            _make("ERROR", "boom2"),
        ]
        pipeline = FilterPipeline([PatternFilter("boom")])
        results = list(context_window(_stream(*lines), pipeline, 1))
        separators = [sep for _, sep in results]
        assert any(separators)

    def test_overlapping_windows_no_separator(self):
        lines = [
            _make("ERROR", "boom1"),
            _make("INFO", "a"),
            _make("ERROR", "boom2"),
        ]
        pipeline = FilterPipeline([PatternFilter("boom")])
        results = list(context_window(_stream(*lines), pipeline, 2))
        separators = [sep for _, sep in results]
        assert not any(separators)

    def test_empty_stream(self):
        pipeline = FilterPipeline([PatternFilter("nothing")])
        results = list(context_window(_stream(), pipeline, 3))
        assert results == []

    def test_no_matches(self):
        lines = [_make("INFO", "a"), _make("INFO", "b")]
        pipeline = FilterPipeline([PatternFilter("boom")])
        results = list(context_window(_stream(*lines), pipeline, 2))
        assert results == []
