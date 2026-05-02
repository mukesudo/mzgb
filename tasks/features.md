# Track: Features
# Owns: context buffer, follow/tail mode, summary mode
# Depends on: backend (FilterPipeline), cli (MVP pipeline wired — Phase 5 complete)
# Parallel-safe with: cli (after MVP), infra (always)

---

## Phase 7 — Context Buffer

- [ ] 7.1 Implement `ContextBuffer(n: int)` in `buffer.py` using `collections.deque(maxlen=n)` for pre-match lines
- [ ] 7.2 Implement post-match countdown counter to collect N lines after each match
- [ ] 7.3 Implement overlap detection: when two match windows are adjacent, merge without inserting a `--` separator
- [ ] 7.4 Render context lines in dimmed style distinct from match lines
- [ ] 7.5 Wire `-C / --context N` Click option and verify: `logsnap -C 3 --pattern "ERROR" app.log` shows 3 lines before and after each match

## Phase 8 — Follow / Tail Mode

- [ ] 8.1 Implement `tail_last_n(file_path, n, parser, pipeline)` in `follow.py` to print the last N matching lines before following
- [ ] 8.2 Implement polling follow loop: `seek` to end of file, sleep 100 ms, read new lines, feed through filter pipeline
- [ ] 8.3 Implement rotation detection: if current file size < last read position, seek to 0 and re-read from start
- [ ] 8.4 Handle `KeyboardInterrupt` (Ctrl+C) cleanly: print nothing extra, exit with code 0
- [ ] 8.5 Wire `--follow` Click flag and verify: `logsnap --follow --level ERROR app.log` streams new errors in real time

## Phase 9 — Summary Mode

- [ ] 9.1 Implement `Aggregator` in `summary.py` that counts matched lines by level as it streams through the pipeline
- [ ] 9.2 Implement top-5 pattern extraction: normalize messages (strip numbers/UUIDs), count occurrences, return top 5
- [ ] 9.3 Render summary as two `rich.table.Table` instances: level counts and top patterns
- [ ] 9.4 Implement exit-code logic: exit with code 1 if any ERROR or FATAL lines were counted
- [ ] 9.5 Verify: `logsnap --summary app.log` prints tables; exit code is 1 when errors present, 0 otherwise
- [ ] 9.6 Verify: `logsnap --summary --level WARN app.log` counts only WARN lines
