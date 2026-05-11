# Changelog

## 0.3.0 (2026-05-08)

### Features
- **Multi-pattern matching** — `--pattern` is now repeatable: `mzgb -p timeout -p refused` matches any line containing either keyword
- `mzgb/matchers.py` — factory `build_matcher(patterns, regex_mode)` auto-selects fastest engine:
  - Single literal → **Boyer-Moore** (`str.find`, no regex overhead)
  - Multiple literals → **Aho-Corasick** automaton O(n) scan (`mzgb[fast]`)
  - Single regex → **Bloom + regex** trigram pre-screen (`mzgb[fast]`)
  - Multiple regexes → **Multi-regex** single compiled alternation
  - No patterns → **Always** no-op matcher
- Hidden `--bench` flag — emits per-stage timing stats and engine name to stderr
- **Drain3 template clustering** — `--summary` groups by log template when `mzgb[drain]` installed; shows top-N patterns deduplicated across similar messages
- `cluster_id` and `template` fields added to `LogLine` dataclass
- Optional dependency groups: `pip install "mzgb[fast]"`, `mzgb[drain]`, `mzgb[all]`

### Bug Fixes
- Fixed silent fallback (`or ""`) in `parse_json_line` and `parse_logfmt_line` — now uses explicit `None` checks per Dawit review

### Tests
- 156 passing (was 118 in v0.2.0)
- New: `tests/unit/test_matchers.py` (28 tests), `tests/unit/test_drain.py` (10 tests)
- Coverage: 89%

### Benchmarks
- `benchmarks/gen_logs.py` + `benchmarks/run.sh` — hyperfine suite vs grep/ripgrep on 4M-line log
- `BENCHMARKS.md` with real results table (Apple M-series, 302MB file)

---

## 0.2.0 (2026-05-06)

### Features
- `--invert` / `-v` — print lines that do **not** match (grep parity)
- `--line-numbers` / `-n` — show 1-based source line number prefix on every matched line
- `--no-color` — explicitly disable ANSI color output (overrides TTY auto-detect)
- Multi-file & glob support — `mzgb *.log --level ERROR` accepts any number of positional file arguments; shell globs are expanded on all platforms
- Filename prefix in multi-file output — dim `filename:` prefix auto-enabled when more than one file is matched
- `--output json` — emit matched lines as NDJSON `{"ts","level","msg","file","lineno"}` (pipes cleanly into `jq`)
- `--output csv` — emit matched lines as CSV with header row (pipes into `pandas`, `miller`, etc.)
- `.bz2` transparent decompression — works alongside existing `.gz` support with zero extra flags
- `--invert` works with `--context` — surrounding context lines are still shown (consistent with `grep -v -C`)

### Tests
- 118 passing (was 99 in v0.1.1)
- New test classes: `TestCLIInvert`, `TestCLILineNumbers`, `TestCLINoColor`, `TestCLIMultiFile`, `TestCLIBz2`, `TestCLIOutputFormat`

---

## 0.1.0 (2026-05-05)

Initial public release.

### Features
- Filter by log level (`--level`, `-l`), repeatable
- Filter by keyword/regex pattern (`--pattern`, `-p`)
- Filter by time range (`--from`, `--to`)
- Context lines before/after matches (`--context`, `-C`)
- Follow mode — tail -f with filtering (`--follow`, `-f`)
- Summary mode — live stats table (`--summary`, `-s`)
- Live progress spinners on TTY for filter, context, and summary modes
- Format auto-detection: plaintext, JSON, logfmt
- Transparent `.gz` support
- Pipe support (`stdin`)
- ANSI color output with level coloring and pattern highlighting
- ASCII art banner on `--help`
- `--version` flag
