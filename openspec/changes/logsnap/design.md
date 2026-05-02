## Context

LogSnap is a greenfield Python CLI tool. There is no existing codebase to migrate from. The constraints are:
- Must handle files too large to fit in memory (target: 5 GB+)
- Must feel fast and responsive to non-expert users
- Must be installable with a single `pip install` and work on macOS, Linux, and WSL
- Python 3.9+ only; no compiled extensions

The tool is composed of five logical layers: input sourcing → parsing → filtering → buffering/aggregation → rendering.

## Goals / Non-Goals

**Goals:**
- Constant-memory streaming over arbitrarily large log files and stdin
- Auto-detect the three most common log formats (plain-text level-prefixed, JSON, logfmt)
- Composable filter pipeline: level + regex + time-range, applied in one pass
- Context-line buffering (N lines before/after each match)
- Live-tail follow mode that feeds through the same filter pipeline
- Summary/stats mode as an alternative output path
- Rich colored terminal output with automatic plain-text fallback
- Clean `--help`, sensible defaults, zero required flags

**Non-Goals:**
- Interactive TUI / pager (out of scope; use `less` for paging)
- Log shipping, aggregation, or storage
- Remote file support (SSH, S3, HTTP)
- Windows native support (WSL is fine)
- Custom log format plugins / configuration files

## Decisions

### 1. Streaming via generator pipeline — not loading file into memory

**Decision**: Read the input source line-by-line using a Python generator chain. Each stage (parse → filter → buffer → render) is a generator that yields to the next.

**Rationale**: A generator pipeline means only one line is in memory at any given stage. This keeps RSS under 50 MB regardless of file size. Loading the file into a list first would OOM on 5 GB files.

**Alternatives considered**: `mmap` — more complex, no advantage for sequential access; `pandas` — far too heavy for a CLI tool.

---

### 2. Click for CLI framework

**Decision**: Use `click` for argument parsing and command structure.

**Rationale**: `click` handles type coercion, `--help` generation, stdin detection (`click.get_text_stream`), and TTY detection out of the box. It is the de facto standard for Python CLIs.

**Alternatives considered**: `argparse` — more verbose, no built-in TTY helpers; `typer` — adds a `pydantic` dependency chain, overkill here.

---

### 3. Auto-detect log format per file, not per line

**Decision**: Sample the first 20 non-empty lines of the file to detect format (JSON, logfmt, or plain-text). Lock in the parser for the rest of the file.

**Rationale**: Format detection per line is expensive and fragile when a file has occasional malformed lines. Sampling the header is fast and reliable for real-world log files which are homogeneous in format.

**Fallback**: If detection is ambiguous, default to plain-text parser (most permissive).

---

### 4. Filter pipeline ordering: level → time-range → regex

**Decision**: Apply filters in this fixed order: level first, time-range second, regex last.

**Rationale**: Level filtering is cheapest (string comparison on a known field) and eliminates the most lines earliest. Time-range is next (numeric comparison). Regex is most expensive and should run on the smallest possible set.

---

### 5. Context buffer using `collections.deque`

**Decision**: Implement pre-match context with a fixed-size `deque(maxlen=N)` that accumulates lines before a match. Post-match context uses a countdown counter.

**Rationale**: `deque(maxlen=N)` is O(1) append and automatically evicts old lines — exactly the right data structure. No custom ring-buffer needed.

---

### 6. Follow mode via polling loop

**Decision**: Implement `--follow` with a `seek`/`read` polling loop (100 ms sleep), not `inotify`/`watchdog`.

**Rationale**: `inotify` is Linux-only and requires an extra dependency. A polling loop works identically on macOS, Linux, and WSL and is simple to implement. 100 ms latency is imperceptible for log tailing.

---

### 7. Rich for output, with TTY detection for fallback

**Decision**: Use `rich.Console` with `force_terminal=False` (default). Rich auto-detects TTY and disables markup/color when piping to a file or another process.

**Rationale**: Zero extra code needed for pipe-friendliness. `rich` is already a dependency for the summary table (`rich.table.Table`), so there is no extra cost.

---

### 8. Project layout — single package `logsnap/`

**Decision**: Structure as a single flat package:
```
logsnap/
  __main__.py       # python -m logsnap entry point
  cli.py            # click commands and options
  parser.py         # log format detection and parsing
  filters.py        # filter pipeline (level, time, regex)
  buffer.py         # context-line deque logic
  follow.py         # tail/follow mode loop
  summary.py        # aggregation and stats
  renderer.py       # rich output formatting
setup.py / pyproject.toml
```

**Rationale**: Flat single-package layout is simple to navigate, easy to test module-by-module, and maps directly to the seven capabilities defined in the proposal.

## Risks / Trade-offs

- **Timestamp parsing performance** → `python-dateutil` is flexible but slow on tight loops. Mitigation: cache the detected format string after the first successful parse and use `datetime.strptime` directly for subsequent lines.
- **Regex performance on large files** → User-supplied regex runs on every line that passes level/time filters. Mitigation: pre-compile the regex once with `re.compile()` and document that catastrophic backtracking is the user's responsibility.
- **Ambiguous log formats** → Some files mix JSON and plain-text lines. Mitigation: the plain-text parser is the fallback and handles mixed files gracefully by treating unparseable lines as raw text (level=UNKNOWN, no timestamp).
- **Follow mode on log rotation** → If the log file is rotated (renamed + recreated), the polling loop will hit EOF and stall. Mitigation: detect file shrinkage (new size < last position) and re-open the file. Document known limitation for symlink rotation.
- **Windows** — explicitly out of scope; polling follow mode may behave differently on Windows file handles.

## Open Questions

- Should `--summary` support `--json` output for machine-readable stats? (Likely yes — defer to tasks phase.)
- Should there be a `--max-matches N` flag to cap output and exit early? (Useful for large files — add as a stretch task.)
- Should `logsnap` support gzip-compressed log files (`.log.gz`)? (Low effort with `gzip.open` — candidate for Phase 3.)
