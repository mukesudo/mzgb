# mzgb

[![Tests](https://img.shields.io/badge/tests-118%20passing-39d353?style=flat-square)](https://github.com/mukesudo/mzgb)
[![Coverage](https://img.shields.io/badge/coverage-91%25-39d353?style=flat-square)](https://github.com/mukesudo/mzgb)
[![PyPI](https://img.shields.io/badge/pypi-v0.2.0-4af0d0?style=flat-square)](https://pypi.org/project/mzgb)
[![Python](https://img.shields.io/badge/python-3.9+-4af0d0?style=flat-square)](https://pypi.org/project/mzgb)
[![License](https://img.shields.io/badge/license-MIT-white?style=flat-square)](LICENSE)

**mzgb** (mezgeb — *"record"* in Amharic) is a fast CLI tool for filtering and navigating very large log files. Streams line by line — no memory issues, no matter the file size.

Filter by log level, regex pattern, or time range. Invert matches, pipe structured JSON/CSV output, scan multiple files at once, and decompress `.gz`/`.bz2` on the fly. Works with plaintext, JSON, and logfmt. Pipes cleanly with `kubectl`, `journalctl`, `cat`, `jq`, and friends.

## Install

```bash
# pip
pip install mzgb

# pipx (isolated, recommended)
pipx install mzgb

# Homebrew (macOS)
brew tap mukesudo/mzgb && brew install mzgb

# Scoop (Windows)
scoop bucket add mzgb https://github.com/mukesudo/scoop-mzgb
scoop install mzgb

# Snap (Linux)
snap install mzgb --classic

# Nix
nix run github:mukesudo/mzgb
```

Or from source:

```bash
git clone https://github.com/mukesudo/mzgb.git
cd mzgb
python3 -m mzgb --help
```

## Usage

```bash
# Filter by log level
mzgb --level ERROR app.log

# Pattern search with context lines
mzgb --pattern "timeout" -C 2 app.log

# Filter by time range
mzgb --from "2024-01-15 14:00" --to "2024-01-15 15:00" app.log

# Invert — everything EXCEPT DEBUG
mzgb --invert --level DEBUG app.log

# Show line numbers
mzgb -n --level ERROR app.log

# Multiple files / globs
mzgb --level ERROR service-a.log service-b.log
mzgb --level ERROR /var/log/*.log

# Structured output — pipe into jq or pandas
mzgb --output json --level ERROR app.log | jq '.msg'
mzgb --output csv app.log > report.csv

# Compressed logs — .gz and .bz2
mzgb --level ERROR archive.log.gz
mzgb --level ERROR archive.log.bz2

# Pipe from anywhere
kubectl logs pod/api | mzgb --level ERROR
journalctl | mzgb --summary

# Follow live logs
mzgb --follow --level ERROR app.log
```

## Options

| Flag | Short | Description |
|------|-------|-------------|
| `--level` | `-l` | Filter by log level (ERROR, WARN, INFO). Repeatable. |
| `--pattern` | `-p` | Filter by keyword or regex. |
| `--from / --to` | | Time range filter. |
| `--context` | `-C` | Show N lines before and after each match. |
| `--invert` | `-v` | Print lines that do **not** match. |
| `--line-numbers` | `-n` | Prefix output with source line number. |
| `--no-color` | | Disable ANSI color output. |
| `--output` | `-o` | Output format: `text` (default), `json`, `csv`. |
| `--summary` | `-s` | Print a summary table instead of raw lines. |
| `--follow` | `-f` | Follow file for new lines (like tail -f). |

## Development

```bash
# Run tests
python -m pytest

# Run with coverage
python -m pytest --cov=mzgb
```

## License

MIT — see [LICENSE](LICENSE)
