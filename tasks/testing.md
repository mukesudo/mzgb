# Track: Testing
# Owns: manual and automated test tasks, added here by any track or person
# Depends on: the feature being tested must be implemented first
# Parallel-safe with: all tracks (tests are added progressively)

---

## How to add a test task

Copy this template and append it under the relevant phase below:

```
- [ ] T-<number> [scope] Description of what to verify
  - Setup: <any prerequisite state>
  - Command: <exact command to run>
  - Expect: <what success looks like>
```

---

## Smoke Tests (manual, run after MVP — Phase 5)

- [ ] T-01 [stream] Pipe a 500 MB file through `logsnap` and verify memory stays below 50 MB
  - Setup: generate a large file with `yes "INFO test" | head -5000000 > /tmp/big.log`
  - Command: `logsnap /tmp/big.log | wc -l`
  - Expect: completes without OOM; RSS stays flat in Activity Monitor

- [ ] T-02 [filter] Level filter returns only matching lines
  - Setup: a mixed-level log file
  - Command: `logsnap --level ERROR test.log | grep -v ERROR`
  - Expect: zero output (no non-ERROR lines leaked through)

- [ ] T-03 [filter] Pattern filter highlights match in TTY output
  - Setup: a log file containing the word "timeout"
  - Command: `logsnap --pattern "timeout" test.log` (in a real terminal)
  - Expect: "timeout" is visually highlighted in each matched line

- [ ] T-04 [pipe] No ANSI codes when piping output
  - Command: `logsnap --level ERROR test.log | cat | grep -P '\x1b'`
  - Expect: zero output (no escape codes)

- [ ] T-05 [cli] No-input error message is clear
  - Command: `logsnap` (with no args and no pipe)
  - Expect: prints a helpful error to stderr, exits with non-zero code

---

## Integration Tests (add as features land)

<!-- Add tasks here as features/follow/summary are implemented -->
