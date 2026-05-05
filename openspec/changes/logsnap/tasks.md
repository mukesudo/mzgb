## 1. Project Infrastructure

- [ ] 1.1 Create `pyproject.toml` with package metadata, entry point `mzgb`, and dependencies (`click`, `rich`, `python-dateutil`)
- [ ] 1.2 Create `mzgb/` package directory with `__init__.py` and `__main__.py` (entry point for `python -m mzgb`)
- [ ] 1.3 Create placeholder module files: `cli.py`, `parser.py`, `filters.py`, `buffer.py`, `follow.py`, `summary.py`, `renderer.py`
- [ ] 1.4 Install the package in editable mode (`pip install -e .`) and verify `mzgb --help` runs without error

## 2. Streaming Engine

- [ ] 2.1 Implement `stream_lines(source)` generator in `cli.py` that accepts a file path or stdin and yields raw text lines one at a time
- [ ] 2.2 Add error handling for permission denied and binary/non-UTF-8 content (decode with replacement, warn to stderr)
- [ ] 2.3 Add error for no-input case (no file path and stdin is a TTY): print clear message and exit non-zero
- [ ] 2.4 Write a manual smoke test: pipe a large file through `mzgb` and confirm memory stays flat

## 3. Log Parser

- [ ] 3.1 Define `LogLine` dataclass with fields: `raw`, `level`, `timestamp`, `message`, `extras`
- [ ] 3.2 Implement `detect_format(lines: list[str]) -> str` that samples up to 20 lines and returns `"json"`, `"logfmt"`, or `"plaintext"`
- [ ] 3.3 Implement `parse_json_line(raw: str) -> LogLine` extracting `level`/`severity`, `message`/`msg`, and common timestamp keys
- [ ] 3.4 Implement `parse_logfmt_line(raw: str) -> LogLine` parsing `key=value` pairs
- [ ] 3.5 Implement `parse_plaintext_line(raw: str) -> LogLine` matching `LEVEL: msg`, `[LEVEL] msg`, and `LEVEL msg` patterns
- [ ] 3.6 Implement timestamp normalization using `python-dateutil`; cache detected format string after first parse for performance
- [ ] 3.7 Wire format detection + parser selection into the streaming pipeline so the correct parser is chosen once per file

## 4. Filter Engine

- [ ] 4.1 Implement `LevelFilter(levels: list[str])` — case-insensitive match; passes all lines when `levels` is empty
- [ ] 4.2 Implement `PatternFilter(pattern: str)` — pre-compile regex with `re.compile()`; raise a clear user-facing error on invalid regex
- [ ] 4.3 Implement `TimeRangeFilter(from_dt, to_dt)` — excludes lines with no timestamp when either bound is set
- [ ] 4.4 Implement `FilterPipeline` that chains filters in order: level → time-range → regex, using AND logic
- [ ] 4.5 Wire `--level`, `--pattern`, `--from`, `--to` Click options into the filter pipeline

## 5. MVP CLI — Phase 1 Complete

- [ ] 5.1 Wire the full pipeline in `cli.py`: `stream_lines` → `detect_format` → `parse` → `FilterPipeline` → print raw output
- [ ] 5.2 Verify end-to-end: `mzgb --level ERROR app.log` returns only error lines
- [ ] 5.3 Verify end-to-end: `cat app.log | mzgb --pattern "timeout"` works via stdin
- [ ] 5.4 Verify end-to-end: `mzgb --from "2024-01-15 14:00" --to "2024-01-15 15:00" app.log` filters by time window

## 6. Output Renderer

- [ ] 6.1 Implement `Renderer` class in `renderer.py` using `rich.Console` with auto-TTY detection
- [ ] 6.2 Add per-level color mapping: ERROR/FATAL=red, WARN=yellow, INFO=green, DEBUG=dim grey
- [ ] 6.3 Implement match highlighting: bold/underline the matched substring when `--pattern` is active and stdout is a TTY
- [ ] 6.4 Render timestamps in dimmed style to reduce visual noise
- [ ] 6.5 Verify plain-text fallback: `mzgb --level ERROR app.log | cat` produces no ANSI escape codes
- [ ] 6.6 Add at least 3 concrete usage examples to `--help` text in `cli.py`

## 7. Context Buffer

- [ ] 7.1 Implement `ContextBuffer(n: int)` in `buffer.py` using `collections.deque(maxlen=n)` for pre-match lines
- [ ] 7.2 Implement post-match countdown counter to collect N lines after each match
- [ ] 7.3 Implement overlap detection: when two match windows are adjacent, merge without inserting a `--` separator
- [ ] 7.4 Render context lines in dimmed style distinct from match lines
- [ ] 7.5 Wire `-C / --context N` Click option and verify: `mzgb -C 3 --pattern "ERROR" app.log` shows 3 lines before and after each match

## 8. Follow / Tail Mode

- [ ] 8.1 Implement `tail_last_n(file_path, n, parser, pipeline)` in `follow.py` to print the last N matching lines before following
- [ ] 8.2 Implement polling follow loop: `seek` to end of file, sleep 100 ms, read new lines, feed through filter pipeline
- [ ] 8.3 Implement rotation detection: if current file size < last read position, seek to 0 and re-read from start
- [ ] 8.4 Handle `KeyboardInterrupt` (Ctrl+C) cleanly: print nothing extra, exit with code 0
- [ ] 8.5 Wire `--follow` Click flag and verify: `mzgb --follow --level ERROR app.log` streams new errors in real time

## 9. Summary Mode

- [ ] 9.1 Implement `Aggregator` in `summary.py` that counts matched lines by level as it streams through the pipeline
- [ ] 9.2 Implement top-5 pattern extraction: normalize messages (strip numbers/UUIDs), count occurrences, return top 5
- [ ] 9.3 Render summary as two `rich.table.Table` instances: level counts and top patterns
- [ ] 9.4 Implement exit-code logic: exit with code 1 if any ERROR or FATAL lines were counted
- [ ] 9.5 Verify: `mzgb --summary app.log` prints tables; exit code is 1 when errors present, 0 otherwise
- [ ] 9.6 Verify: `mzgb --summary --level WARN app.log` counts only WARN lines

## 10. Polish and Robustness

- [ ] 10.1 Add `--max-matches N` flag to cap output and exit after N matched lines (useful for exploration on huge files)
- [ ] 10.2 Add gzip support: auto-detect `.gz` extension and open with `gzip.open` transparently
- [ ] 10.3 Write unit tests for `detect_format`, each parser, `FilterPipeline`, and `ContextBuffer`
- [ ] 10.4 Write a README with installation instructions, feature overview, and 10 example commands
- [ ] 10.5 Final end-to-end test: run all core scenarios against a generated 100 MB synthetic log file and confirm correctness and performance targets
