# mzgb PM Dashboard
_Updated: 2026-05-10 00:30 UTC_

---

## 🚀 v0.3 — SHIPPED (2026-05-10)

**7/7 algorithm tasks DONE — 156 tests passing**

| Feature | Status |
|---|---|
| `mzgb/matchers.py` factory — `build_matcher(patterns, regex_mode)` | ✅ |
| Multi-pattern `--pattern` (repeatable, OR logic) | ✅ |
| Boyer-Moore literal fast path (`str.find`) | ✅ |
| Aho-Corasick multi-pattern engine (`mzgb[fast]`) | ✅ |
| Bloom filter pre-screen (`mzgb[fast]`) | ✅ |
| Drain3 template clustering in `--summary` (`mzgb[drain]`) | ✅ |
| Benchmark suite vs grep/ripgrep with real results | ✅ |

**Shipped:**
- `pip install "mzgb[fast]"` — Aho-Corasick + Bloom
- `pip install "mzgb[drain]"` — Drain3 clustering
- `pip install "mzgb[all]"` — everything
- BENCHMARKS.md with honest performance analysis
- Hidden `--bench` flag for per-stage timing

---

## ✅ v0.2 — SHIPPED (2026-05-06)

**8/8 quick-win tasks DONE — 118 tests passing**

| Feature | Status |
|---|---|
| `--invert` / `-v` (grep parity) | ✅ |
| `--line-numbers` / `-n` | ✅ |
| `--no-color` flag | ✅ |
| Multi-file + glob support | ✅ |
| Filename prefix in multi-file output | ✅ |
| `--output json` (NDJSON) | ✅ |
| `--output csv` (with header) | ✅ |
| `.bz2` transparent decompression | ✅ |

---

## ✅ v0.1.1 — SHIPPED (2026-05-05)

**All 31 v0.1 tasks: DONE (100%)**

| Item | Status |
|---|---|
| Core CLI (`--level`, `--pattern`, `--from`, `--to`, `-C`, `--follow`, `--summary`) | ✅ |
| 99 passing tests · 91% coverage | ✅ |
| PyPI / pipx / Homebrew / Scoop / Snap / Nix | ✅ |

---

## 🎯 Next: v0.4 — Intelligence (the moat)

| Task | Effort |
|---|---|
| `--dedupe` — exact + template deduplication | medium |
| Spike detector — 1-min buckets, mean+2σ warning | medium |
| `--timeline` — ASCII bar chart (▁▂▃▄▅▆▇█) | small |
| `.mzgb.toml` config loader | medium |
| `--interactive` TUI mode using `textual` | large |

---

## Agents — Status

| Agent | Role | Status |
|---|---|---|
| Biruk | Backend — parser, filters, streaming | IDLE |
| Liya | CLI — Click wiring, renderer | IDLE |
| Tigist | Features — buffer, follow, summary | IDLE |
| Natnael | Infra — scaffold, tests, README | IDLE |
| Selam | Reviewer — code review gate | IDLE |
| Endalk | Release — merge sequencer | IDLE |
| Dawit | Senior reviewer — pre-commit gate | ACTIVE |

---

## Rooms
- #mzgb-general — announcements
- #mzgb-integration — READY/MERGE signals
- #mzgb-blockers — failures and escalations

---

## Key Links
- PyPI: https://pypi.org/project/mzgb/0.3.0/
- GitHub (public): https://github.com/mukesudo/mzgb
- GitHub (dev): https://github.com/mukesudo/mzgb-dev
- Homebrew tap: https://github.com/mukesudo/homebrew-mzgb
- Scoop bucket: https://github.com/mukesudo/scoop-mzgb
- Landing page: https://mzgb.netlify.app
