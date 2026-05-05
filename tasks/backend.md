# Track: Backend
# Owns: log parser, filter engine, streaming engine, context buffer
# Depends on: infra (package scaffold must exist first)
# Parallel-safe with: features, cli (once package scaffold is done)

---

## Phase 2 — Streaming Engine

- [ ] 2.1 Implement `stream_lines(source)` generator in `cli.py` that accepts a file path or stdin and yields raw text lines one at a time
- [ ] 2.2 Add error handling for permission denied and binary/non-UTF-8 content (decode with replacement, warn to stderr)
- [ ] 2.3 Add error for no-input case (no file path and stdin is a TTY): print clear message and exit non-zero
- [ ] 2.4 Write a manual smoke test: pipe a large file through `mzgb` and confirm memory stays flat

## Phase 3 — Log Parser

- [ ] 3.1 Define `LogLine` dataclass with fields: `raw`, `level`, `timestamp`, `message`, `extras`
- [ ] 3.2 Implement `detect_format(lines: list[str]) -> str` that samples up to 20 lines and returns `"json"`, `"logfmt"`, or `"plaintext"`
- [ ] 3.3 Implement `parse_json_line(raw: str) -> LogLine` extracting `level`/`severity`, `message`/`msg`, and common timestamp keys
- [ ] 3.4 Implement `parse_logfmt_line(raw: str) -> LogLine` parsing `key=value` pairs
- [ ] 3.5 Implement `parse_plaintext_line(raw: str) -> LogLine` matching `LEVEL: msg`, `[LEVEL] msg`, and `LEVEL msg` patterns
- [ ] 3.6 Implement timestamp normalization using `python-dateutil`; cache detected format string after first parse for performance
- [ ] 3.7 Wire format detection + parser selection into the streaming pipeline so the correct parser is chosen once per file

## Phase 4 — Filter Engine

- [ ] 4.1 Implement `LevelFilter(levels: list[str])` — case-insensitive match; passes all lines when `levels` is empty
- [ ] 4.2 Implement `PatternFilter(pattern: str)` — pre-compile regex with `re.compile()`; raise a clear user-facing error on invalid regex
- [ ] 4.3 Implement `TimeRangeFilter(from_dt, to_dt)` — excludes lines with no timestamp when either bound is set
- [ ] 4.4 Implement `FilterPipeline` that chains filters in order: level → time-range → regex, using AND logic
- [ ] 4.5 Wire `--level`, `--pattern`, `--from`, `--to` Click options into the filter pipeline
