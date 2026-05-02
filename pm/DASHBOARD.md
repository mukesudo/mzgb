# LogSnap PM Dashboard

_Will be updated automatically by Endalk after every merge._

## Progress
- **0/30 tasks done** (0%)

## Agents
- Biruk (Backend) — parser, filters, streaming
- Liya (CLI) — Click wiring, renderer
- Tigist (Features) — buffer, follow, summary
- Natnael (Infra) — scaffold, tests, README
- Selam (Reviewer) — code review gate
- Endalk (Release) — merge sequencer

## Signal Protocol
```
REVIEW:task_id|agent    → triggers Selam code review
MERGE:task_id|title|agent → triggers Endalk merge + commit
READY: <module>         → unblocks dependent agents
SHIP-READY ✓            → Natnael: full E2E suite green
```
