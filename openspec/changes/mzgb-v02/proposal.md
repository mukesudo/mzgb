## Why

mzgb v0.1.1 is live on PyPI, Homebrew, Scoop, Snap, and Nix. The core streaming engine is solid (99 tests, 91% coverage). The next phase closes the gap with `grep`/`ripgrep` on UX, adds smarter matching algorithms, and builds the intelligence features that no other CLI log tool has.

## Business Value

v0.1 solved the *"I have a huge log file"* problem. v0.2 solves the *"I want to work the way I already know"* problem — users coming from grep expect `--invert`, line numbers, glob support, and JSON output. These are table-stakes features before mzgb can be recommended by engineers as a daily driver.

### Priority: **HIGH**

- Low implementation cost, high retention impact
- Each feature removes a reason to fall back to grep
- JSON/CSV output unlocks scripting and pipeline use cases
- Compressed file support is essential for production on-call scenarios

## What Changes

### v0.2 — Quick wins (~2–3 weeks)

**UX:**
- `--invert` / `-v` — print lines that do NOT match (core grep parity)
- `--line-numbers` / `-n` — show original line number prefix
- `--no-color` — explicit color disable flag (currently auto-detect only)

**Input/Output:**
- Multi-file and glob support — `mzgb *.log --level ERROR`
- `--output json` / `--output csv` — structured output for piping into jq, pandas
- `.bz2` compressed file support alongside existing `.gz`

### v0.3 — Algorithms (~3–4 weeks)

- **Aho-Corasick multi-pattern engine** — single-pass scan for multiple `--pattern` flags (`pyahocorasick`)
- **Boyer-Moore literal search** — faster path for non-regex patterns (the 80% case)
- **Bloom filter pre-screening** — probabilistic line skipping for rare patterns in INFO-heavy logs
- **Drain log template parser** — cluster log lines into templates for smarter `--summary`

### v0.4 — Intelligence (~4–6 weeks)

- **`--dedupe`** — collapse repeated lines with `(×N)` count suffix
- **Anomaly/spike detection** — flag time windows where error rate exceeds mean+2σ
- **Frequency timeline** — ASCII bar chart of log volume per minute/hour
- **Interactive TUI** — `--interactive` scrollable viewer with live filter toggles (textual)
- **`.mzgb.toml` config** — per-project defaults for level, time format, patterns

## New Capabilities

- `invert-filter`: Boolean flag to negate the active filter predicate
- `line-numbering`: Track and display source file line numbers through the streaming pipeline
- `multi-file-input`: Accept multiple file arguments or glob patterns via `fileinput`
- `structured-output`: Emit NDJSON or CSV records per matched line
- `compressed-input`: Transparent `.bz2` decompression alongside existing `.gz`
- `aho-corasick-matcher`: Multi-pattern automaton for O(n+m+z) scanning
- `drain-parser`: Log template clustering via drain3 for semantic deduplication
- `spike-detector`: Rolling window statistical anomaly detection on error rates
- `tui-mode`: textual-based interactive log browser
- `config-file`: TOML config loader with CWD-upward discovery

## Impact

- **New optional deps**: `pyahocorasick`, `drain3`, `textual`, `tomli` (3.9/3.10 only)
- All new deps are optional — install extras: `pip install mzgb[tui]`, `mzgb[fast]`
- No breaking changes to existing CLI interface
- Test coverage target: maintain ≥ 90%
