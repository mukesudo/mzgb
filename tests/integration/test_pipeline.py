"""Integration tests — filter pipeline + parser working together (Phase 5)."""
import pytest


class TestParserFilterIntegration:
    def test_level_filter_on_plaintext_file(self, plaintext_log):
        from logsnap.parser import detect_format, parse_plaintext_line
        from logsnap.filters import LevelFilter, FilterPipeline

        lines = plaintext_log.read_text().splitlines()
        fmt = detect_format(lines[:20])
        assert fmt == "plaintext"

        pipeline = FilterPipeline([LevelFilter(["ERROR"])])
        parsed = [parse_plaintext_line(l) for l in lines]
        matched = [l for l in parsed if pipeline.match(l)]

        assert all(l.level == "ERROR" for l in matched)
        assert len(matched) == 2

    def test_pattern_filter_on_json_file(self, json_log):
        from logsnap.parser import detect_format, parse_json_line
        from logsnap.filters import PatternFilter, FilterPipeline

        lines = json_log.read_text().splitlines()
        fmt = detect_format(lines[:20])
        assert fmt == "json"

        pipeline = FilterPipeline([PatternFilter("Connection")])
        parsed = [parse_json_line(l) for l in lines]
        matched = [l for l in parsed if pipeline.match(l)]

        assert len(matched) == 1
        assert "Connection" in matched[0].message

    def test_combined_level_and_pattern_filter(self, plaintext_log):
        from logsnap.parser import parse_plaintext_line
        from logsnap.filters import LevelFilter, PatternFilter, FilterPipeline

        lines = plaintext_log.read_text().splitlines()
        pipeline = FilterPipeline([LevelFilter(["ERROR"]), PatternFilter("Connection")])
        matched = [l for l in (parse_plaintext_line(l) for l in lines) if pipeline.match(l)]

        assert all(l.level == "ERROR" for l in matched)
        assert all("Connection" in (l.message or "") for l in matched)


class TestStreamingIntegration:
    def test_stream_lines_yields_all_lines(self, plaintext_log):
        from logsnap.cli import stream_lines
        result = list(stream_lines(str(plaintext_log)))
        assert len(result) == 7

    def test_stream_large_file_memory(self, large_log):
        import tracemalloc
        from logsnap.cli import stream_lines

        tracemalloc.start()
        for _ in stream_lines(str(large_log)):
            pass
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert peak < 50 * 1024 * 1024, f"Peak memory {peak // 1024 // 1024} MB exceeded 50 MB"
