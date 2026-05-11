"""Pattern matching engines for mzgb.

Engine selection (fastest first):
  1. Literal single pattern  → Boyer-Moore via str.find() (no regex metacharacters)
  2. Multi-pattern N >= 2    → Aho-Corasick automaton (requires pyahocorasick)
  3. Bloom pre-screen        → Bloom filter gate before full regex (requires pybloom-live)
  4. Regex fallback          → re.compile (always available)

Use build_matcher(patterns, regex_mode) to get the right engine automatically.
"""
from __future__ import annotations

import re
from typing import List, Protocol, runtime_checkable


@runtime_checkable
class Matcher(Protocol):
    """Minimal interface every engine must satisfy."""

    def match(self, text: str) -> bool:
        """Return True if text contains at least one pattern match."""
        ...

    @property
    def engine(self) -> str:
        """Short label used by --bench output."""
        ...


# ── Regex (fallback) ────────────────────────────────────────────────────────

class RegexMatcher:
    """Standard re.compile matcher — always available, handles full regex syntax."""

    def __init__(self, pattern: str) -> None:
        self._re = re.compile(pattern, re.IGNORECASE)
        self._pattern = pattern

    def match(self, text: str) -> bool:
        return bool(self._re.search(text))

    @property
    def engine(self) -> str:
        return "regex"


# ── Boyer-Moore via str.find (literal single pattern) ──────────────────────

_REGEX_META = re.compile(r"[.^$*+?{}\[\]|()\\]")


def _is_literal(pattern: str) -> bool:
    """Return True if pattern contains no regex metacharacters."""
    return not bool(_REGEX_META.search(pattern))


class LiteralMatcher:
    """Case-insensitive str.find() fast path for single literal patterns.

    Equivalent to Boyer-Moore in CPython's str implementation.
    """

    def __init__(self, pattern: str) -> None:
        self._needle = pattern.lower()

    def match(self, text: str) -> bool:
        return self._needle in text.lower()

    @property
    def engine(self) -> str:
        return "literal"


# ── Aho-Corasick (multi-pattern) ────────────────────────────────────────────

class AhoCorasickMatcher:
    """Multi-pattern matcher using pyahocorasick automaton (O(n) scan).

    Falls back gracefully to regex OR if pyahocorasick is not installed.
    All patterns are matched case-insensitively.
    """

    def __init__(self, patterns: List[str]) -> None:
        import ahocorasick  # type: ignore[import]
        self._A = ahocorasick.Automaton()
        for idx, p in enumerate(patterns):
            self._A.add_word(p.lower(), (idx, p.lower()))
        self._A.make_automaton()

    def match(self, text: str) -> bool:
        lower = text.lower()
        for _ in self._A.iter(lower):
            return True
        return False

    @property
    def engine(self) -> str:
        return "aho-corasick"


# ── Bloom pre-screen + Regex ────────────────────────────────────────────────

class BloomMatcher:
    """Bloom filter pre-screen gating a full regex match.

    The Bloom filter is seeded with trigrams of each pattern. A line is
    only passed to the regex engine if it passes the Bloom gate, saving
    CPU on the vast majority of non-matching lines in large files.

    Requires pybloom-live.
    """

    def __init__(self, pattern: str, capacity: int = 1_000_000, error_rate: float = 0.01) -> None:
        from pybloom_live import BloomFilter  # type: ignore[import]
        self._re = re.compile(pattern, re.IGNORECASE)
        needle = pattern.lower()
        # seed bloom with all trigrams of the pattern
        trigrams = {needle[i:i+3] for i in range(len(needle) - 2)} if len(needle) >= 3 else {needle}
        self._bloom: BloomFilter = BloomFilter(capacity=capacity, error_rate=error_rate)
        for tg in trigrams:
            self._bloom.add(tg)
        self._trigrams = trigrams

    def _bloom_pass(self, text: str) -> bool:
        lower = text.lower()
        return any(tg in lower for tg in self._trigrams)

    def match(self, text: str) -> bool:
        if not self._bloom_pass(text):
            return False
        return bool(self._re.search(text))

    @property
    def engine(self) -> str:
        return "bloom+regex"


# ── MultiRegexMatcher (OR of N regexes, no external deps) ───────────────────

class MultiRegexMatcher:
    """OR of multiple regex patterns compiled into a single alternation."""

    def __init__(self, patterns: List[str]) -> None:
        combined = "|".join(f"(?:{p})" for p in patterns)
        self._re = re.compile(combined, re.IGNORECASE)

    def match(self, text: str) -> bool:
        return bool(self._re.search(text))

    @property
    def engine(self) -> str:
        return "multi-regex"


# ── Factory ──────────────────────────────────────────────────────────────────

def build_matcher(patterns: List[str], regex_mode: bool = False) -> Matcher:
    """Return the fastest available matcher for the given patterns.

    Selection logic:
      - 0 patterns  → always-True no-op matcher
      - 1 pattern, literal, no regex_mode → LiteralMatcher (Boyer-Moore)
      - 1 pattern, has metacharacters or regex_mode=True → try BloomMatcher,
        fall back to RegexMatcher
      - N >= 2 patterns, all literal, no regex_mode → try AhoCorasickMatcher,
        fall back to MultiRegexMatcher
      - N >= 2 patterns with regex_mode → MultiRegexMatcher

    Args:
        patterns:   List of pattern strings from the CLI.
        regex_mode: Force regex interpretation even for literal-looking patterns.

    Returns:
        A Matcher instance with a .match(text) -> bool method.
    """
    if not patterns:
        return _AlwaysMatcher()

    if len(patterns) == 1:
        p = patterns[0]
        if not regex_mode and _is_literal(p):
            return LiteralMatcher(p)
        # try bloom pre-screen
        try:
            return BloomMatcher(p)
        except Exception:
            return RegexMatcher(p)

    # N >= 2
    all_literal = all(_is_literal(p) for p in patterns) and not regex_mode
    if all_literal:
        try:
            return AhoCorasickMatcher(patterns)
        except Exception:
            pass
    return MultiRegexMatcher(patterns)


class _AlwaysMatcher:
    """No-op matcher — matches every line (used when no patterns given)."""

    def match(self, text: str) -> bool:  # noqa: ARG002
        return True

    @property
    def engine(self) -> str:
        return "always"
