# mzgb PM Dashboard
_Updated: 2026-05-06 11:00 UTC_

---

## 🚀 v0.1.1 — SHIPPED

**All 31 v0.1 tasks: DONE (100%)**

### What shipped
| Item | Status |
|---|---|
| Core CLI (`--level`, `--pattern`, `--from`, `--to`, `-C`, `--follow`, `--summary`) | ✅ |
| 99 passing tests · 91% coverage | ✅ |
| PyPI — `pip install mzgb` | ✅ |
| pipx — `pipx install mzgb` | ✅ |
| Homebrew tap — `brew tap mukesudo/mzgb` | ✅ |
| Scoop bucket — `scoop bucket add mzgb ...` | ✅ |
| Snap — `snap/snapcraft.yaml` ready (pending snapcraft upload) | ✅ |
| Nix flake — `nix run github:mukesudo/mzgb` | ✅ |
| GitHub Actions OIDC publish workflow | ✅ |
| Landing page — mzgb.netlify.app | ✅ |
| GitHub release v0.1.0 + v0.1.1 with dist assets | ✅ |
| `asciinema` + `agg` installed — demo recording ready | ✅ |

---

## � v0.2 — SHIPPED (2026-05-06)

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

## � Next: v0.3 — Algorithms

**0/10 tasks started** — OpenSpec: `openspec/changes/mzgb-v02/`

### Backlog (priority order)
| Task | Effort | Agent |
|---|---|---|
| `mzgb/matchers.py` factory | medium | Biruk |
| Aho-Corasick multi-pattern engine | medium | Biruk |
| Boyer-Moore literal search fast path | small | Biruk |
| Bloom filter pre-screen | medium | Biruk |
| Drain template parser for `--summary` | medium | Tigist |
| Benchmark suite vs grep/ripgrep | medium | Natnael |
| `BENCHMARKS.md` results table | small | Natnael |

### Then v0.4 (intelligence — the moat)
- `--dedupe`, spike detection, timeline chart
- Interactive TUI (`textual`)
- `.mzgb.toml` config file

---

## Agents — Status

| Agent | Role | Status |
|---|---|---|
| Biruk | Backend — parser, filters, streaming | IDLE — awaiting v0.2 kickoff |
| Liya | CLI — Click wiring, renderer | IDLE — awaiting v0.2 kickoff |
| Tigist | Features — buffer, follow, summary | IDLE |
| Natnael | Infra — scaffold, tests, README | IDLE |
| Selam | Reviewer — code review gate | IDLE |
| Endalk | Release — merge sequencer | IDLE |
| Dawit | Senior reviewer — pre-commit gate | ACTIVE (pre-commit hook) |

## Rooms
- #mzgb-general — announcements
- #mzgb-integration — READY/MERGE signals
- #mzgb-blockers — failures and escalations

---

## Key Links
- PyPI: https://pypi.org/project/mzgb/0.1.1/
- GitHub (public): https://github.com/mukesudo/mzgb
- GitHub (dev): https://github.com/mukesudo/mzgb-dev
- Homebrew tap: https://github.com/mukesudo/homebrew-mzgb
- Scoop bucket: https://github.com/mukesudo/scoop-mzgb
- Landing page: https://mzgb.netlify.app
