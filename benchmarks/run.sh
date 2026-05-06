#!/usr/bin/env bash
# Benchmark mzgb vs grep vs ripgrep using hyperfine.
# Requires: hyperfine, grep, rg (ripgrep), mzgb
#
# Usage:
#   cd <project-root>
#   bash benchmarks/run.sh               # uses benchmarks/bench.log (generate first)
#   LOG=custom.log bash benchmarks/run.sh

set -euo pipefail

LOG="${LOG:-benchmarks/bench.log}"
OUT="benchmarks/results.md"

if [[ ! -f "$LOG" ]]; then
  echo "Log file not found: $LOG"
  echo "Run: python3 benchmarks/gen_logs.py"
  exit 1
fi

echo "Log file : $LOG ($(du -sh "$LOG" | cut -f1))"
echo "Running benchmarks…"
echo ""

hyperfine \
  --warmup 2 \
  --runs 5 \
  --export-markdown "$OUT" \
  --command-name "mzgb --level ERROR" \
    "mzgb --level ERROR --no-color '$LOG' > /dev/null" \
  --command-name "grep ERROR" \
    "grep -i ' ERROR ' '$LOG' > /dev/null" \
  --command-name "rg ERROR" \
    "rg -i ' ERROR ' '$LOG' > /dev/null" \
  --command-name "mzgb --pattern timeout" \
    "mzgb --pattern timeout --no-color '$LOG' > /dev/null" \
  --command-name "grep timeout" \
    "grep -i timeout '$LOG' > /dev/null" \
  --command-name "rg timeout" \
    "rg -i timeout '$LOG' > /dev/null" \
  --command-name "mzgb --pattern timeout (literal)" \
    "mzgb --pattern timeout --no-color '$LOG' > /dev/null" \
  --command-name "mzgb --bench --pattern timeout" \
    "mzgb --bench --pattern timeout --no-color '$LOG' > /dev/null"

echo ""
echo "Results written to $OUT"
