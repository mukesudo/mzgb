# Task Coordination

Multi-agent task tracks for parallel implementation of mzgb.
`openspec/changes/mzgb/tasks.md` is the **single source of truth**.
Track files here are read-only work queues for each agent/person.

## Track Files

| File | Owns | Unblocked by |
|---|---|---|
| `infra.md` | Scaffold, packaging, tests, README | Nothing — start here |
| `backend.md` | Streaming engine, parser, filter engine | Phase 1 (infra) |
| `cli.md` | Click wiring, output renderer, help | Phase 1 (infra) + backend |
| `features.md` | Context buffer, follow mode, summary | Phase 5 MVP (cli + backend) |
| `testing.md` | Manual and automated test tasks | Feature being tested |

## Dependency Order

```
infra (Phase 1)
    ↓
backend (Phases 2–4) ──┐
cli (Phases 1, 5–6)  ──┤→ features (Phases 7–9) → infra (Phase 10)
testing (ongoing)    ──┘
```

## How to Add a Task

Open the relevant track file and append a checkbox under the correct phase:

```markdown
- [ ] 7.6 Description of the new task
```

Then mirror it in `openspec/changes/mzgb/tasks.md` under the same phase
to keep the source of truth in sync.

## Syncing Checkboxes

When you check off tasks in `tasks.md`, propagate to track files:

```bash
# See what's out of sync
python tasks/distribute.py

# Apply the sync
python tasks/distribute.py --apply
```

## How to Add a Test Task

Open `testing.md` and append under the appropriate section using this template:

```markdown
- [ ] T-<number> [scope] What to verify
  - Setup: <prerequisite state>
  - Command: <exact command>
  - Expect: <what success looks like>
```

Example:
```markdown
- [ ] T-06 [follow] Follow mode streams new lines in real time
  - Setup: `touch /tmp/live.log`
  - Command: run `mzgb --follow /tmp/live.log` in one terminal, append lines in another
  - Expect: new lines appear immediately (within ~100 ms)
```
