#!/usr/bin/env python3
"""Generate a synthetic log file for benchmarking mzgb vs grep vs ripgrep.

Usage:
    python3 benchmarks/gen_logs.py                  # writes bench.log (~500 MB)
    python3 benchmarks/gen_logs.py --lines 5000000  # custom line count
    python3 benchmarks/gen_logs.py --out /tmp/b.log
"""
import argparse
import random
import sys
from datetime import datetime, timedelta

LEVELS = ["DEBUG", "INFO", "INFO", "INFO", "WARN", "ERROR", "ERROR", "FATAL"]

MESSAGES = [
    "Connection timeout after 30s",
    "User login successful uid={}",
    "Request processed in {}ms path=/api/v1/users",
    "Cache miss for key=session:{}",
    "DB query failed: relation {} does not exist",
    "Retrying connection attempt={} delay={}s",
    "File not found: /var/log/app/{}.log",
    "Memory usage {}% — threshold 85%",
    "Shutdown signal received",
    "Worker {} started pid={}",
    "Health check OK latency={}ms",
    "Rate limit exceeded ip=192.168.{}.{}",
    "OOM killer invoked on process {}",
    "TLS handshake failed peer={}",
    "Queue depth={} processing backlog",
]

SERVICES = ["api", "worker", "scheduler", "proxy", "db", "cache", "auth"]


def gen_line(ts: datetime) -> str:
    level = random.choice(LEVELS)
    svc = random.choice(SERVICES)
    msg_tpl = random.choice(MESSAGES)
    msg = msg_tpl.format(
        random.randint(1, 9999),
        random.randint(1, 999),
        random.randint(1, 255),
        random.randint(1, 255),
    )
    ts_str = ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return f"{ts_str}  {level:<8}  [{svc}]  {msg}\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic log file")
    parser.add_argument("--lines", type=int, default=4_000_000,
                        help="Number of lines to generate (default: 4,000,000 ≈ 500 MB)")
    parser.add_argument("--out", default="benchmarks/bench.log",
                        help="Output file path")
    args = parser.parse_args()

    ts = datetime(2024, 1, 15, 0, 0, 0)
    delta = timedelta(milliseconds=50)

    print(f"Generating {args.lines:,} lines → {args.out}", file=sys.stderr)
    written = 0
    with open(args.out, "w", buffering=1 << 20) as fh:
        for i in range(args.lines):
            fh.write(gen_line(ts))
            ts += delta
            written += 1
            if written % 500_000 == 0:
                print(f"  {written:,} / {args.lines:,}", file=sys.stderr)
    print(f"Done. File: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
