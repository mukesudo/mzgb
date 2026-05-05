# Track: Infra
# Owns: project scaffold, packaging, tests, README, polish
# Depends on: nothing (starts first — unblocks all other tracks)
# Parallel-safe with: backend, cli, features (after Phase 1 scaffold is done)

---

## Phase 1 — Project Infrastructure

- [x] 1.1 Create `pyproject.toml` with package metadata, entry point `mzgb`, and dependencies (`click`, `rich`, `python-dateutil`)
- [ ] 1.2 Create `mzgb/` package directory with `__init__.py` and `__main__.py` (entry point for `python -m mzgb`)
- [ ] 1.3 Create placeholder module files: `cli.py`, `parser.py`, `filters.py`, `buffer.py`, `follow.py`, `summary.py`, `renderer.py`
- [ ] 1.4 Install the package in editable mode (`pip install -e .`) and verify `mzgb --help` runs without error

## Phase 10 — Polish and Robustness

- [ ] 10.1 Add `--max-matches N` flag to cap output and exit after N matched lines (useful for exploration on huge files)
- [ ] 10.2 Add gzip support: auto-detect `.gz` extension and open with `gzip.open` transparently
- [ ] 10.3 Write unit tests for `detect_format`, each parser, `FilterPipeline`, and `ContextBuffer`
- [ ] 10.4 Write a README with installation instructions, feature overview, and 10 example commands
- [ ] 10.5 Final end-to-end test: run all core scenarios against a generated 100 MB synthetic log file and confirm correctness and performance targets
