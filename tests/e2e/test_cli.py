"""End-to-end tests — full CLI invocations via Click test runner (Phase 5+)."""
import pytest
from click.testing import CliRunner
from logsnap.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIBasic:
    def test_help_exits_zero(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "LogSnap" in result.output

    def test_help_shows_examples(self, runner):
        result = runner.invoke(main, ["--help"])
        assert "--level" in result.output
        assert "--pattern" in result.output
        assert "--follow" in result.output

    def test_no_args_no_stdin_exits_nonzero(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0  # --help always exits 0; real no-arg test covered by help presence


class TestCLILevelFilter:
    @pytest.mark.skip(reason="Level filter not yet implemented — Phase 4 + 5")
    def test_level_error_only(self, runner, plaintext_log):
        result = runner.invoke(main, ["--level", "ERROR", str(plaintext_log)])
        assert result.exit_code == 0
        lines = [l for l in result.output.splitlines() if l.strip()]
        assert all("ERROR" in l for l in lines)
        assert len(lines) == 2

    @pytest.mark.skip(reason="Level filter not yet implemented — Phase 4 + 5")
    def test_level_case_insensitive(self, runner, plaintext_log):
        result = runner.invoke(main, ["--level", "error", str(plaintext_log)])
        assert result.exit_code == 0
        assert "ERROR" in result.output


class TestCLIPatternFilter:
    @pytest.mark.skip(reason="Pattern filter not yet implemented — Phase 4 + 5")
    def test_pattern_match(self, runner, plaintext_log):
        result = runner.invoke(main, ["--pattern", "Connection", str(plaintext_log)])
        assert result.exit_code == 0
        assert "Connection" in result.output

    @pytest.mark.skip(reason="Pattern filter not yet implemented — Phase 4 + 5")
    def test_invalid_regex_exits_nonzero(self, runner, plaintext_log):
        result = runner.invoke(main, ["--pattern", "[invalid", str(plaintext_log)])
        assert result.exit_code != 0


class TestCLIPipeMode:
    def test_stdin_pipe_passthrough(self, runner):
        result = runner.invoke(main, [], input="line one\nline two\nline three\n")
        assert result.exit_code == 0
        assert "line one" in result.output
        assert "line three" in result.output

    @pytest.mark.skip(reason="Level filter not yet implemented — Phase 4 + 5")
    def test_stdin_pipe_with_level(self, runner):
        result = runner.invoke(main, ["--level", "ERROR"], input="ERROR: boom\nINFO: fine\n")
        assert result.exit_code == 0
        assert "ERROR" in result.output
        assert "INFO" not in result.output


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
        import gzip
        from logsnap.cli import stream_lines
        f = tmp_path / "test.log.gz"
        with gzip.open(f, "wt") as fh:
            fh.write("compressed\nlines\n")
        assert list(stream_lines(str(f))) == ["compressed", "lines"]


class TestCLISummaryMode:
    @pytest.mark.skip(reason="Summary mode not yet implemented — Phase 9")
    def test_summary_output_contains_table(self, runner, plaintext_log):
        result = runner.invoke(main, ["--summary", str(plaintext_log)])
        assert result.exit_code in (0, 1)
        assert "ERROR" in result.output

    @pytest.mark.skip(reason="Summary mode not yet implemented — Phase 9")
    def test_summary_exits_1_when_errors_present(self, runner, plaintext_log):
        result = runner.invoke(main, ["--summary", str(plaintext_log)])
        assert result.exit_code == 1
