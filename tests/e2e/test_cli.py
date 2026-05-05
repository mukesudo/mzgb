"""End-to-end tests — full CLI invocations via Click test runner."""
import gzip
import textwrap

import pytest
from click.testing import CliRunner

from logsnap.cli import main


@pytest.fixture
def runner():
    return CliRunner()


# ── Basic ──────────────────────────────────────────────────────────────────────

class TestCLIBasic:
    def test_help_exits_zero(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "LogSnap" in result.output

    def test_help_shows_flags(self, runner):
        result = runner.invoke(main, ["--help"])
        for flag in ["--level", "--pattern", "--follow", "--summary", "--context"]:
            assert flag in result.output

    def test_nonexistent_file_exits_nonzero(self, runner):
        result = runner.invoke(main, ["/tmp/does_not_exist_xyz.log"])
        assert result.exit_code != 0


# ── Level filter ───────────────────────────────────────────────────────────────

class TestCLILevelFilter:
    def test_error_only(self, runner, plaintext_log):
        result = runner.invoke(main, ["--level", "ERROR", str(plaintext_log)])
        assert result.exit_code == 0
        lines = [l for l in result.output.splitlines() if l.strip()]
        assert len(lines) == 2
        assert all("ERROR" in l for l in lines)

    def test_case_insensitive(self, runner, plaintext_log):
        result = runner.invoke(main, ["--level", "error", str(plaintext_log)])
        assert result.exit_code == 0
        assert "ERROR" in result.output

    def test_multi_level(self, runner, plaintext_log):
        result = runner.invoke(main, ["--level", "ERROR", "--level", "WARN", str(plaintext_log)])
        assert result.exit_code == 0
        lines = [l for l in result.output.splitlines() if l.strip()]
        assert any("ERROR" in l for l in lines)
        assert any("WARN" in l for l in lines)
        assert not any("INFO" in l for l in lines)

    def test_no_match_produces_empty_output(self, runner, plaintext_log):
        result = runner.invoke(main, ["--level", "TRACE", str(plaintext_log)])
        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_json_format_level_filter(self, runner, json_log):
        result = runner.invoke(main, ["--level", "ERROR", str(json_log)])
        assert result.exit_code == 0
        assert "ERROR" in result.output
        assert "DEBUG" not in result.output

    def test_logfmt_format_level_filter(self, runner, logfmt_log):
        result = runner.invoke(main, ["--level", "ERROR", str(logfmt_log)])
        assert result.exit_code == 0
        assert "ERROR" in result.output
        assert "DEBUG" not in result.output


# ── Pattern filter ─────────────────────────────────────────────────────────────

class TestCLIPatternFilter:
    def test_keyword_match(self, runner, plaintext_log):
        result = runner.invoke(main, ["--pattern", "Connection", str(plaintext_log)])
        assert result.exit_code == 0
        assert "Connection" in result.output

    def test_regex_match(self, runner, plaintext_log):
        result = runner.invoke(main, ["--pattern", r"ERROR.*db:\d+", str(plaintext_log)])
        assert result.exit_code == 0
        assert "db:5432" in result.output

    def test_case_insensitive_pattern(self, runner, plaintext_log):
        result = runner.invoke(main, ["--pattern", "connection", str(plaintext_log)])
        assert result.exit_code == 0
        assert "Connection" in result.output

    def test_invalid_regex_exits_nonzero(self, runner, plaintext_log):
        result = runner.invoke(main, ["--pattern", "[invalid", str(plaintext_log)])
        assert result.exit_code != 0

    def test_pattern_combined_with_level(self, runner, plaintext_log):
        result = runner.invoke(main, ["--level", "ERROR", "--pattern", "Connection", str(plaintext_log)])
        assert result.exit_code == 0
        lines = [l for l in result.output.splitlines() if l.strip()]
        assert all("ERROR" in l and "Connection" in l for l in lines)


# ── Time range filter ──────────────────────────────────────────────────────────

class TestCLITimeRange:
    def test_from_filter(self, runner, plaintext_log):
        result = runner.invoke(main, ["--from", "2024-01-15 14:00:10", str(plaintext_log)])
        assert result.exit_code == 0
        lines = [l for l in result.output.splitlines() if l.strip()]
        assert len(lines) >= 1
        assert all("14:00:0" not in l or int(l.split("14:00:0")[1][0]) >= 9 for l in lines)

    def test_to_filter(self, runner, plaintext_log):
        result = runner.invoke(main, ["--to", "2024-01-15 14:00:02", str(plaintext_log)])
        assert result.exit_code == 0
        lines = [l for l in result.output.splitlines() if l.strip()]
        assert len(lines) == 2

    def test_from_to_range(self, runner, plaintext_log):
        result = runner.invoke(main, [
            "--from", "2024-01-15 14:00:05",
            "--to",   "2024-01-15 14:00:11",
            str(plaintext_log)
        ])
        assert result.exit_code == 0
        lines = [l for l in result.output.splitlines() if l.strip()]
        assert len(lines) == 3

    def test_invalid_from_exits_nonzero(self, runner, plaintext_log):
        result = runner.invoke(main, ["--from", "not-a-date", str(plaintext_log)])
        assert result.exit_code != 0


# ── Context mode ───────────────────────────────────────────────────────────────

class TestCLIContext:
    def test_context_includes_surrounding_lines(self, runner, plaintext_log):
        result = runner.invoke(main, ["--level", "ERROR", "--context", "1", str(plaintext_log)])
        assert result.exit_code == 0
        assert "ERROR" in result.output
        assert "Retrying" in result.output or "WARN" in result.output or "INFO" in result.output

    def test_context_zero_same_as_default(self, runner, plaintext_log):
        r1 = runner.invoke(main, ["--level", "ERROR", str(plaintext_log)])
        r2 = runner.invoke(main, ["--level", "ERROR", "--context", "0", str(plaintext_log)])
        assert r1.output == r2.output

    def test_context_separator_between_groups(self, runner, tmp_path):
        f = tmp_path / "sep.log"
        f.write_text(
            "2024-01-15 14:00:01 INFO  a\n"
            "2024-01-15 14:00:02 ERROR first\n"
            "2024-01-15 14:00:03 INFO  b\n"
            "2024-01-15 14:00:04 INFO  c\n"
            "2024-01-15 14:00:05 INFO  d\n"
            "2024-01-15 14:00:06 ERROR second\n"
            "2024-01-15 14:00:07 INFO  e\n"
        )
        result = runner.invoke(main, ["--level", "ERROR", "--context", "1", str(f)])
        assert result.exit_code == 0
        assert "first" in result.output
        assert "second" in result.output
        assert "--" in result.output


# ── Summary mode ───────────────────────────────────────────────────────────────

class TestCLISummaryMode:
    def test_summary_contains_total(self, runner, plaintext_log):
        result = runner.invoke(main, ["--summary", str(plaintext_log)])
        assert result.exit_code == 0
        assert "Total" in result.output

    def test_summary_contains_error_count(self, runner, plaintext_log):
        result = runner.invoke(main, ["--summary", str(plaintext_log)])
        assert result.exit_code == 0
        assert "ERROR" in result.output

    def test_summary_contains_time_range(self, runner, plaintext_log):
        result = runner.invoke(main, ["--summary", str(plaintext_log)])
        assert result.exit_code == 0
        assert "2024" in result.output

    def test_summary_json_format(self, runner, json_log):
        result = runner.invoke(main, ["--summary", str(json_log)])
        assert result.exit_code == 0
        assert "ERROR" in result.output
        assert "Total" in result.output


# ── Pipe / stdin ───────────────────────────────────────────────────────────────

class TestCLIPipeMode:
    def test_stdin_passthrough(self, runner):
        result = runner.invoke(main, [], input="line one\nline two\nline three\n")
        assert result.exit_code == 0
        assert "line one" in result.output
        assert "line three" in result.output

    def test_stdin_level_filter(self, runner):
        result = runner.invoke(main, ["--level", "ERROR"], input="ERROR: boom\nINFO: fine\n")
        assert result.exit_code == 0
        assert "ERROR" in result.output
        assert "INFO" not in result.output

    def test_stdin_summary(self, runner):
        data = "2024-01-15 14:00:01 ERROR boom\n2024-01-15 14:00:02 INFO ok\n"
        result = runner.invoke(main, ["--summary"], input=data)
        assert result.exit_code == 0
        assert "ERROR" in result.output
        assert "Total" in result.output


# ── Streaming / large file ─────────────────────────────────────────────────────

class TestCLILargeFile:
    def test_large_file_completes(self, runner, large_log):
        result = runner.invoke(main, ["--level", "ERROR", str(large_log)])
        assert result.exit_code == 0

    def test_large_file_correct_count(self, runner, large_log):
        result = runner.invoke(main, ["--level", "ERROR", str(large_log)])
        lines = [l for l in result.output.splitlines() if l.strip()]
        assert len(lines) == 2_000

    def test_large_file_summary(self, runner, large_log):
        result = runner.invoke(main, ["--summary", str(large_log)])
        assert result.exit_code == 0
        assert "10,000" in result.output or "10000" in result.output

    def test_large_file_pattern(self, runner, large_log):
        result = runner.invoke(main, ["--pattern", "Message number 9999", str(large_log)])
        assert result.exit_code == 0
        assert "9999" in result.output


# ── gzip support ───────────────────────────────────────────────────────────────

class TestStreamLines:
    def test_stream_lines_from_file(self, tmp_path):
        from logsnap.cli import stream_lines
        f = tmp_path / "test.log"
        f.write_text("alpha\nbeta\ngamma\n")
        assert list(stream_lines(str(f))) == ["alpha", "beta", "gamma"]

    def test_stream_lines_strips_newline(self, tmp_path):
        from logsnap.cli import stream_lines
        f = tmp_path / "test.log"
        f.write_text("hello\n")
        assert list(stream_lines(str(f))) == ["hello"]

    def test_stream_lines_gzip(self, tmp_path):
        from logsnap.cli import stream_lines
        f = tmp_path / "test.log.gz"
        with gzip.open(f, "wt") as fh:
            fh.write("compressed\nlines\n")
        assert list(stream_lines(str(f))) == ["compressed", "lines"]

    def test_gzip_level_filter(self, runner, tmp_path):
        f = tmp_path / "app.log.gz"
        content = textwrap.dedent("""\
            2024-01-15 14:00:01 INFO  ok
            2024-01-15 14:00:02 ERROR boom
        """)
        with gzip.open(f, "wt") as fh:
            fh.write(content)
        result = runner.invoke(main, ["--level", "ERROR", str(f)])
        assert result.exit_code == 0
        assert "ERROR" in result.output
        assert "INFO" not in result.output


# ── Edge cases ─────────────────────────────────────────────────────────────────

class TestCLIEdgeCases:
    def test_empty_file(self, runner, tmp_path):
        f = tmp_path / "empty.log"
        f.write_text("")
        result = runner.invoke(main, [str(f)])
        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_single_line_file(self, runner, tmp_path):
        f = tmp_path / "one.log"
        f.write_text("2024-01-15 14:00:01 ERROR single\n")
        result = runner.invoke(main, ["--level", "ERROR", str(f)])
        assert result.exit_code == 0
        assert "single" in result.output

    def test_unicode_content(self, runner, tmp_path):
        f = tmp_path / "unicode.log"
        f.write_text("2024-01-15 14:00:01 ERROR tëst üñícode 日本語\n", encoding="utf-8")
        result = runner.invoke(main, ["--level", "ERROR", str(f)])
        assert result.exit_code == 0
        assert "ERROR" in result.output

    def test_no_newline_at_eof(self, runner, tmp_path):
        f = tmp_path / "nonl.log"
        f.write_bytes(b"2024-01-15 14:00:01 ERROR no newline")
        result = runner.invoke(main, ["--level", "ERROR", str(f)])
        assert result.exit_code == 0
        assert "ERROR" in result.output

    def test_summary_empty_file(self, runner, tmp_path):
        f = tmp_path / "empty.log"
        f.write_text("")
        result = runner.invoke(main, ["--summary", str(f)])
        assert result.exit_code == 0
        assert "0" in result.output
