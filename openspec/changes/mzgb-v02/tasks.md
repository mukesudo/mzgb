## v0.2 — Quick Wins

### UX

- [x] 2.1.1 Add `--invert` / `-v` boolean flag to `cli.py`; wrap filter predicate: `not matches(line) if invert else matches(line)`
- [x] 2.1.2 Add `--line-numbers` / `-n` flag; track counter in stream loop; render as dim right-aligned prefix `  42 │`
- [x] 2.1.3 Add `--no-color` flag; pass to `rich.Console(no_color=True)` to override TTY auto-detect

### Input / Output

- [x] 2.2.1 Replace single `file` argument with `files` (multiple via `nargs=-1`); wire through `fileinput.input(files)`
- [x] 2.2.2 Prefix output lines with dim filename when more than one file is provided; add `--filename / -H` to force/suppress
- [x] 2.2.3 Add `--output [text|json|csv]` option; `json` emits NDJSON `{"ts","level","msg","file","lineno"}`; `csv` uses `csv.writer`
- [x] 2.2.4 Add `.bz2` transparent decompression alongside existing `.gz` in file open path
- [x] 2.2.5 Write unit tests for multi-file, `--output json`, `--invert`, `--line-numbers`

## v0.3 — Algorithms

### Pattern Matching

- [ ] 3.1.1 Create `mzgb/matchers.py` with factory `build_matcher(patterns, regex_mode)` returning the right engine
- [ ] 3.1.2 Implement Aho-Corasick path: `pyahocorasick` automaton for N ≥ 2 patterns; install as optional dep `mzgb[fast]`
- [ ] 3.1.3 Implement Boyer-Moore path: detect literal (no regex metacharacters) single patterns; use `str.find()` fast path
- [ ] 3.1.4 Implement Bloom filter pre-screen: `pybloom-live` n-gram seed per pattern; gate full matcher on bloom pass
- [ ] 3.1.5 Add hidden `--bench` flag emitting per-stage timing stats to stderr
- [ ] 3.1.6 Write benchmark: `benchmarks/gen_logs.py` (500 MB synthetic file) + `benchmarks/run.sh` using `hyperfine`
- [ ] 3.1.7 Write `BENCHMARKS.md` table comparing mzgb vs grep vs ripgrep on level filter + pattern search tasks

### Buffering & Structure

- [ ] 3.2.1 Integrate `drain3` in `mzgb/parser.py`; stream each line through `drain.add_log_message()` to get cluster ID
- [ ] 3.2.2 Update `--summary` to group by Drain template cluster ID, not raw line text; show top-N templates with counts
- [ ] 3.2.3 Write unit tests for matchers factory, Aho-Corasick path, Drain integration

## v0.4 — Intelligence

### Analysis

- [ ] 4.1.1 Implement `--dedupe` flag: exact dedup via `dict` counting seen lines; print with `(×N)` suffix on flush
- [ ] 4.1.2 Implement template dedup using Drain cluster ID as key when `drain3` available
- [ ] 4.1.3 Implement spike detector: bucket lines into 1-min windows, compute rolling mean+2σ, emit `[SPIKE]` warning lines
- [ ] 4.1.4 Implement `--timeline` flag: collect per-minute buckets, render ASCII bar chart using block chars `▁▂▃▄▅▆▇█`

### Experience

- [ ] 4.2.1 Implement `.mzgb.toml` config loader: walk CWD upward, parse with `tomllib`/`tomli`, merge with CLI flags (CLI wins)
- [ ] 4.2.2 Implement `--interactive` TUI mode using `textual`: scrollable DataTable, key bindings `e/w/i/d` for level toggles, `/` for search
- [ ] 4.2.3 Write unit tests for config loader, spike detector, dedup logic

## Infra & Promotion (ongoing)

- [ ] I.1 Record asciinema demo (30–45 sec): generate 200 MB log, show level filter, summary, pipe; convert to GIF with `agg`
- [ ] I.2 Embed demo GIF at top of README; add "Why mzgb" section with 4-bullet comparison vs grep/lnav/ELK
- [ ] I.3 Add `pepy.tech` download badge to README once first week of PyPI downloads is visible
- [ ] I.4 Post Show HN after v0.3 ships (algorithms are real — include benchmark numbers)
- [ ] I.5 Write dev.to article: "Boyer-Moore and Aho-Corasick in practice — building a fast log filter CLI" (post after v0.3)
- [ ] I.6 Submit to AUR (Arch Linux) — single `PKGBUILD` file
- [ ] I.7 Submit to conda-forge — `meta.yaml` PR to staged-recipes
