# mzgb AI Agents

Four Ethiopian-named agents coordinate mzgb implementation via **task files + Matrix chat**.

```
┌──────────────┐                              ┌──────────────┐
│   Biruk      │◀────── Task Files ──────────▶│    Liya      │
│  (Backend)   │    tasks/backend.md          │   (CLI)      │
│ parser.py    │    tasks/cli.md              │ cli.py       │
│ filters.py   │                              │ renderer.py  │
└──────┬───────┘                              └──────┬───────┘
       │                                             │
       │           Matrix Chat Rooms                 │
       └──────────────────┬──────────────────────────┘
                          │
              ┌───────────┴────────────┐
              │                        │
       ┌──────┴───────┐        ┌───────┴──────┐
       │   Tigist     │        │   Natnael    │
       │  (Features)  │        │  (Infra)     │
       │ buffer.py    │        │ scaffold     │
       │ follow.py    │        │ tests        │
       │ summary.py   │        │ README       │
       └──────────────┘        └──────────────┘
```

---

## The Agents

### Biruk — Backend Engineer
**ብርሃን ለሁሉ** — *"Light for all"* | *Biruk = Blessed*

- **Track:** `tasks/backend.md` | Phases 2–4
- **Owns:** `mzgb/parser.py`, `mzgb/filters.py`, `stream_lines()`
- **Posts to:** `#mzgb-integration` → `READY: filter-engine` when done
- **Unblocks:** Liya (Phase 5) and Tigist (Phase 7)

---

### Liya — CLI & Output Renderer
**ልያ** — *"Great one"*

- **Track:** `tasks/cli.md` | Phases 1, 5–6
- **Owns:** `mzgb/cli.py`, `mzgb/renderer.py`
- **Waits for:** `READY: filter-engine` from Biruk before Phase 5
- **Posts to:** `#mzgb-integration` → `READY: cli-mvp` when done
- **Unblocks:** Tigist (Phase 7)

---

### Tigist — Features Engineer
**ትግስት** — *"Patience"*

- **Track:** `tasks/features.md` | Phases 7–9
- **Owns:** `mzgb/buffer.py`, `mzgb/follow.py`, `mzgb/summary.py`
- **Waits for:** BOTH `READY: filter-engine` AND `READY: cli-mvp`
- **Posts to:** `#mzgb-integration` → `READY: context-buffer`, `READY: follow-mode`, `READY: summary-mode`
- **Unblocks:** Natnael (Phase 10)

---

### Natnael — Infrastructure & Testing
**ናትናኤል** — *"Gift of God"*

- **Track:** `tasks/infra.md` | Phases 1 + 10
- **Owns:** `pyproject.toml`, `setup.cfg`, `tests/`, `README.md`
- **Starts immediately** (Phase 1 has no dependencies)
- **Waits for:** `READY: all-features` from Tigist before Phase 10
- **Posts:** `SHIP-READY ✓` to `#mzgb-general` when full test suite passes

---

## Matrix Rooms

| Room | Purpose |
|---|---|
| `#mzgb-general` | All agents online/offline announcements |
| `#mzgb-backend` | Biruk's work updates + spec questions |
| `#mzgb-cli` | Liya's work updates |
| `#mzgb-features` | Tigist's work updates |
| `#mzgb-infra` | Natnael's work updates |
| `#mzgb-integration` | Cross-agent READY signals + coordination |
| `#mzgb-blockers` | Failed tests, design questions, escalations |

---

## Signal Protocol

Agents coordinate via structured messages in `#mzgb-integration`:

```
READY: filter-engine   ← Biruk posts when Phases 2-4 done
READY: cli-mvp         ← Liya posts when Phase 5 done
READY: context-buffer  ← Tigist posts when Phase 7 done
READY: follow-mode     ← Tigist posts when Phase 8 done
READY: summary-mode    ← Tigist posts when Phase 9 done
READY: all-features    ← Tigist posts when Phases 7-9 all done
SHIP-READY ✓           ← Natnael posts when full E2E suite green
```

To confirm an implementation task (unblock an agent):
```
DONE:2.1   ← posts this in the agent's room to confirm task 2.1 is implemented
```

---

## Setup & Running

### 1. Start the Matrix homeserver
```bash
cd matrix/
docker compose up -d
# Wait ~15 seconds for Synapse to start
```

### 2. Bootstrap rooms and agent accounts (once)
```bash
pip3 install aiohttp matrix-nio
python3 agents/bootstrap.py
```

### 3. Start agents (each in a separate terminal)
```bash
python3 agents/natnael.py   # Start first — sets up scaffold
python3 agents/biruk.py     # Backend pipeline
python3 agents/liya.py      # CLI wiring (waits for Biruk)
python3 agents/tigist.py    # Features (waits for Biruk + Liya)
```

### 4. Join as a human (optional)
Connect any Matrix client (Element, Cinny) to `http://localhost:8008`.
Register as yourself and join the rooms. You can post `DONE:X.Y` messages
to confirm tasks, flag blockers, or just watch the coordination unfold.
