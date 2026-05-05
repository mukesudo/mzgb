# mzgb

[![Tests](https://img.shields.io/badge/tests-44%20passing-39d353?style=flat-square)](https://github.com/mukesudo/mzgb)
[![Coverage](https://img.shields.io/badge/coverage-85%25-39d353?style=flat-square)](https://github.com/mukesudo/mzgb)
[![Python](https://img.shields.io/badge/python-3.9+-4af0d0?style=flat-square)](https://pypi.org/project/mzgb)
[![License](https://img.shields.io/badge/license-MIT-white?style=flat-square)](LICENSE)
[![Landing page](https://img.shields.io/badge/website-mzgb.netlify.app-4af0d0?style=flat-square)](https://mzgb.netlify.app)

A CLI tool for filtering large log files by level, pattern, and time range. Streams line by line — works on files of any size.

## Install

```bash
pip install mzgb
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

# Pipe from anywhere
kubectl logs pod/api | mzgb --level ERROR
journalctl | mzgb --summary

# Follow live logs
mzgb --follow --level ERROR app.log
```

## Options

| Flag | Description |
|------|-------------|
| `--level` | Filter by log level (ERROR, WARN, INFO). Repeatable. |
| `--pattern` | Filter by keyword or regex. |
| `--from / --to` | Time range filter. |
| `-C / --context` | Show N lines before and after each match. |
| `--summary` | Print a summary table instead of raw lines. |
| `--follow` | Follow file for new lines (like tail -f). |

## Development

```bash
# Run tests
python -m pytest

# Run with coverage
python -m pytest --cov=mzgb
```

## License

MIT — see [LICENSE](LICENSE)
