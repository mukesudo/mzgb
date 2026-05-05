"""Unit tests — filter engine (Phase 4)."""
import pytest
from mzgb.parser import LogLine


def make_line(level=None, message="test message", timestamp=None):
    return LogLine(raw=f"{level} {message}", level=level, message=message, timestamp=timestamp)


class TestLevelFilter:
    def test_single_level_passes(self):
        from mzgb.filters import LevelFilter
        f = LevelFilter(["ERROR"])
        assert f.match(make_line(level="ERROR")) is True

    def test_single_level_blocks(self):
        from mzgb.filters import LevelFilter
        f = LevelFilter(["ERROR"])
        assert f.match(make_line(level="INFO")) is False

    def test_multiple_levels(self):
        from mzgb.filters import LevelFilter
        f = LevelFilter(["ERROR", "WARN"])
        assert f.match(make_line(level="WARN")) is True
        assert f.match(make_line(level="DEBUG")) is False

    def test_empty_levels_passes_all(self):
        from mzgb.filters import LevelFilter
        f = LevelFilter([])
        assert f.match(make_line(level="DEBUG")) is True

    def test_case_insensitive(self):
        from mzgb.filters import LevelFilter
        f = LevelFilter(["error"])
        assert f.match(make_line(level="ERROR")) is True


class TestPatternFilter:
    def test_keyword_match(self):
        from mzgb.filters import PatternFilter
        f = PatternFilter("timeout")
        assert f.match(make_line(message="connection timeout occurred")) is True

    def test_keyword_no_match(self):
        from mzgb.filters import PatternFilter
        f = PatternFilter("timeout")
        assert f.match(make_line(message="everything is fine")) is False

    def test_regex_match(self):
        from mzgb.filters import PatternFilter
        f = PatternFilter(r"user_id=\d+")
        assert f.match(make_line(message="login user_id=42 success")) is True

    def test_invalid_regex_raises(self):
        from mzgb.filters import PatternFilter
        import re
        with pytest.raises((re.error, SystemExit, ValueError)):
            PatternFilter("[invalid")


class TestTimeRangeFilter:
    def test_within_range_passes(self):
        from mzgb.filters import TimeRangeFilter
        from datetime import datetime
        f = TimeRangeFilter(
            from_dt=datetime(2024, 1, 15, 14, 0, 0),
            to_dt=datetime(2024, 1, 15, 15, 0, 0),
        )
        line = make_line(timestamp=datetime(2024, 1, 15, 14, 30, 0))
        assert f.match(line) is True

    def test_outside_range_blocked(self):
        from mzgb.filters import TimeRangeFilter
        from datetime import datetime
        f = TimeRangeFilter(
            from_dt=datetime(2024, 1, 15, 14, 0, 0),
            to_dt=datetime(2024, 1, 15, 15, 0, 0),
        )
        line = make_line(timestamp=datetime(2024, 1, 15, 16, 0, 0))
        assert f.match(line) is False

    def test_no_timestamp_excluded(self):
        from mzgb.filters import TimeRangeFilter
        from datetime import datetime
        f = TimeRangeFilter(from_dt=datetime(2024, 1, 15, 14, 0, 0), to_dt=None)
        assert f.match(make_line(timestamp=None)) is False


class TestFilterPipeline:
    def test_and_logic_all_pass(self):
        from mzgb.filters import LevelFilter, PatternFilter, FilterPipeline
        pipeline = FilterPipeline([LevelFilter(["ERROR"]), PatternFilter("timeout")])
        line = make_line(level="ERROR", message="connection timeout")
        assert pipeline.match(line) is True

    def test_and_logic_one_fails(self):
        from mzgb.filters import LevelFilter, PatternFilter, FilterPipeline
        pipeline = FilterPipeline([LevelFilter(["ERROR"]), PatternFilter("timeout")])
        line = make_line(level="INFO", message="connection timeout")
        assert pipeline.match(line) is False
