# Changelog

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
