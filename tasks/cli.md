# Track: CLI
# Owns: Click commands, output renderer, help text, MVP wiring
# Depends on: infra (package scaffold), backend (FilterPipeline, parser must be importable)
# Parallel-safe with: features (after Phase 5 MVP is green)

---

## Phase 1 — Project Infrastructure (shared with infra track)

- [ ] 1.1 Create `pyproject.toml` with package metadata, entry point `mzgb`, and dependencies (`click`, `rich`, `python-dateutil`)
- [ ] 1.2 Create `mzgb/` package directory with `__init__.py` and `__main__.py` (entry point for `python -m mzgb`)
- [ ] 1.3 Create placeholder module files: `cli.py`, `parser.py`, `filters.py`, `buffer.py`, `follow.py`, `summary.py`, `renderer.py`
- [ ] 1.4 Install the package in editable mode (`pip install -e .`) and verify `mzgb --help` runs without error

## Phase 5 — MVP CLI

- [ ] 5.1 Wire the full pipeline in `cli.py`: `stream_lines` → `detect_format` → `parse` → `FilterPipeline` → print raw output
- [ ] 5.2 Verify end-to-end: `mzgb --level ERROR app.log` returns only error lines
- [ ] 5.3 Verify end-to-end: `cat app.log | mzgb --pattern "timeout"` works via stdin
- [ ] 5.4 Verify end-to-end: `mzgb --from "2024-01-15 14:00" --to "2024-01-15 15:00" app.log` filters by time window

## Phase 6 — Output Renderer

- [ ] 6.1 Implement `Renderer` class in `renderer.py` using `rich.Console` with auto-TTY detection
- [ ] 6.2 Add per-level color mapping: ERROR/FATAL=red, WARN=yellow, INFO=green, DEBUG=dim grey
- [ ] 6.3 Implement match highlighting: bold/underline the matched substring when `--pattern` is active and stdout is a TTY
- [ ] 6.4 Render timestamps in dimmed style to reduce visual noise
- [ ] 6.5 Verify plain-text fallback: `mzgb --level ERROR app.log | cat` produces no ANSI escape codes
- [ ] 6.6 Add at least 3 concrete usage examples to `--help` text in `cli.py`
