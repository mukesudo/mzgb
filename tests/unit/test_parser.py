"""Unit tests — log parser (Phase 3)."""
import pytest
from logsnap.parser import LogLine


class TestLogLineDataclass:
    def test_raw_field_required(self):
        line = LogLine(raw="some raw log line")
        assert line.raw == "some raw log line"

    def test_defaults_are_none(self):
        line = LogLine(raw="x")
        assert line.level is None
        assert line.timestamp is None
        assert line.message is None
        assert line.extras == {}

    def test_extras_is_independent_per_instance(self):
        a = LogLine(raw="a")
        b = LogLine(raw="b")
        a.extras["key"] = "value"
        assert "key" not in b.extras


# ── These tests are stubs that will pass once parser functions are implemented ──

class TestDetectFormat:
    @pytest.mark.skip(reason="detect_format not yet implemented — Phase 3.2")
    def test_detects_json(self):
        from logsnap.parser import detect_format
        lines = ['{"level": "INFO", "msg": "hello"}'] * 5
        assert detect_format(lines) == "json"

    @pytest.mark.skip(reason="detect_format not yet implemented — Phase 3.2")
    def test_detects_logfmt(self):
        from logsnap.parser import detect_format
        lines = ['level=INFO msg="hello"'] * 5
        assert detect_format(lines) == "logfmt"

    @pytest.mark.skip(reason="detect_format not yet implemented — Phase 3.2")
    def test_falls_back_to_plaintext(self):
        from logsnap.parser import detect_format
        lines = ["INFO hello world"] * 5
        assert detect_format(lines) == "plaintext"


class TestPlaintextParser:
    @pytest.mark.skip(reason="parse_plaintext_line not yet implemented — Phase 3.5")
    def test_parses_level_colon_format(self):
        from logsnap.parser import parse_plaintext_line
        line = parse_plaintext_line("ERROR: connection refused")
        assert line.level == "ERROR"
        assert "connection refused" in line.message

    @pytest.mark.skip(reason="parse_plaintext_line not yet implemented — Phase 3.5")
    def test_parses_bracket_level_format(self):
        from logsnap.parser import parse_plaintext_line
        line = parse_plaintext_line("[WARN] disk usage high")
        assert line.level == "WARN"

    @pytest.mark.skip(reason="parse_plaintext_line not yet implemented — Phase 3.5")
    def test_malformed_line_does_not_crash(self):
        from logsnap.parser import parse_plaintext_line
        line = parse_plaintext_line("\x00\xff binary garbage")
        assert line.level is None or line.level == "UNKNOWN"


class TestJsonParser:
    @pytest.mark.skip(reason="parse_json_line not yet implemented — Phase 3.3")
    def test_parses_level_and_msg(self):
        from logsnap.parser import parse_json_line
        line = parse_json_line('{"level": "ERROR", "msg": "boom", "time": "2024-01-15T14:00:10Z"}')
        assert line.level == "ERROR"
        assert line.message == "boom"
        assert line.timestamp is not None

    @pytest.mark.skip(reason="parse_json_line not yet implemented — Phase 3.3")
    def test_accepts_severity_key(self):
        from logsnap.parser import parse_json_line
        line = parse_json_line('{"severity": "WARN", "message": "disk high"}')
        assert line.level == "WARN"

    @pytest.mark.skip(reason="parse_json_line not yet implemented — Phase 3.3")
    def test_invalid_json_does_not_crash(self):
        from logsnap.parser import parse_json_line
        line = parse_json_line("not json at all")
        assert line.level is None or line.level == "UNKNOWN"


class TestLogfmtParser:
    @pytest.mark.skip(reason="parse_logfmt_line not yet implemented — Phase 3.4")
    def test_parses_level_and_msg(self):
        from logsnap.parser import parse_logfmt_line
        line = parse_logfmt_line('level=ERROR msg="connection refused"')
        assert line.level == "ERROR"
        assert "connection refused" in line.message
