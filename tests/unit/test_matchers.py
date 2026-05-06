"""Unit tests for mzgb.matchers — engine selection and correctness."""
import pytest

from mzgb.matchers import (
    LiteralMatcher,
    MultiRegexMatcher,
    RegexMatcher,
    _AlwaysMatcher,
    _is_literal,
    build_matcher,
)


# ── _is_literal ──────────────────────────────────────────────────────────────

class TestIsLiteral:
    def test_plain_word(self) -> None:
        assert _is_literal("timeout") is True

    def test_has_dot(self) -> None:
        assert _is_literal("a.b") is False

    def test_has_star(self) -> None:
        assert _is_literal("err*") is False

    def test_has_brackets(self) -> None:
        assert _is_literal("[ERROR]") is False

    def test_plain_with_spaces(self) -> None:
        assert _is_literal("connection refused") is True


# ── LiteralMatcher ───────────────────────────────────────────────────────────

class TestLiteralMatcher:
    def test_match_exact(self) -> None:
        m = LiteralMatcher("timeout")
        assert m.match("Connection timeout at 14:00") is True

    def test_no_match(self) -> None:
        m = LiteralMatcher("timeout")
        assert m.match("Everything is fine") is False

    def test_case_insensitive(self) -> None:
        m = LiteralMatcher("ERROR")
        assert m.match("error: something went wrong") is True

    def test_engine_label(self) -> None:
        assert LiteralMatcher("x").engine == "literal"


# ── RegexMatcher ─────────────────────────────────────────────────────────────

class TestRegexMatcher:
    def test_match_regex(self) -> None:
        m = RegexMatcher(r"err\w+")
        assert m.match("error: disk full") is True

    def test_no_match(self) -> None:
        m = RegexMatcher(r"err\w+")
        assert m.match("all good") is False

    def test_case_insensitive(self) -> None:
        m = RegexMatcher("ERROR")
        assert m.match("error occurred") is True

    def test_engine_label(self) -> None:
        assert RegexMatcher("x").engine == "regex"


# ── MultiRegexMatcher ────────────────────────────────────────────────────────

class TestMultiRegexMatcher:
    def test_matches_first(self) -> None:
        m = MultiRegexMatcher(["timeout", "refused"])
        assert m.match("Connection timeout") is True

    def test_matches_second(self) -> None:
        m = MultiRegexMatcher(["timeout", "refused"])
        assert m.match("Connection refused") is True

    def test_no_match(self) -> None:
        m = MultiRegexMatcher(["timeout", "refused"])
        assert m.match("All systems nominal") is False

    def test_engine_label(self) -> None:
        assert MultiRegexMatcher(["a"]).engine == "multi-regex"


# ── _AlwaysMatcher ────────────────────────────────────────────────────────────

class TestAlwaysMatcher:
    def test_always_true(self) -> None:
        m = _AlwaysMatcher()
        assert m.match("anything") is True
        assert m.match("") is True

    def test_engine_label(self) -> None:
        assert _AlwaysMatcher().engine == "always"


# ── build_matcher factory ────────────────────────────────────────────────────

class TestBuildMatcher:
    def test_no_patterns_returns_always(self) -> None:
        m = build_matcher([])
        assert m.engine == "always"
        assert m.match("whatever") is True

    def test_single_literal_returns_literal(self) -> None:
        m = build_matcher(["timeout"])
        assert m.engine == "literal"

    def test_single_regex_returns_regex_or_bloom(self) -> None:
        m = build_matcher(["err\\w+"])
        assert m.engine in ("regex", "bloom+regex")

    def test_single_literal_regex_mode_forces_regex(self) -> None:
        m = build_matcher(["timeout"], regex_mode=True)
        assert m.engine in ("regex", "bloom+regex")

    def test_multi_literal_no_aho_falls_back_to_multi_regex(self) -> None:
        m = build_matcher(["timeout", "refused"])
        assert m.engine in ("aho-corasick", "multi-regex")

    def test_multi_regex_mode(self) -> None:
        m = build_matcher(["err\\w+", "warn\\w+"], regex_mode=True)
        assert m.engine == "multi-regex"

    def test_literal_matcher_correctness(self) -> None:
        m = build_matcher(["timeout"])
        assert m.match("Connection timeout") is True
        assert m.match("All good") is False

    def test_multi_pattern_correctness(self) -> None:
        m = build_matcher(["timeout", "refused"])
        assert m.match("Connection refused") is True
        assert m.match("Connection timeout") is True
        assert m.match("All good") is False

    def test_regex_pattern_correctness(self) -> None:
        m = build_matcher([r"err\w+"])
        assert m.match("error: disk full") is True
        assert m.match("warning: low memory") is False
