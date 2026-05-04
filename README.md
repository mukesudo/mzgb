# logsnap

[![Tests](https://img.shields.io/badge/tests-44%20passing-39d353?style=flat-square)](https://github.com/mukesudo/logsnap)
[![Coverage](https://img.shields.io/badge/coverage-85%25-39d353?style=flat-square)](https://github.com/mukesudo/logsnap)
[![Python](https://img.shields.io/badge/python-3.9+-4af0d0?style=flat-square)](https://pypi.org/project/logsnap)
[![License](https://img.shields.io/badge/license-MIT-white?style=flat-square)](LICENSE)
[![Landing page](https://img.shields.io/badge/website-logsnap.netlify.app-4af0d0?style=flat-square)](https://logsnap.netlify.app)

A CLI tool for filtering large log files by level, pattern, and time range. Streams line by line — works on files of any size.

## Install

```bash
pip install logsnap
```

Or from source:

```bash
git clone https://github.com/mukesudo/logsnap.git
cd logsnap
python3 -m logsnap --help
```

## Usage

```bash
# Filter by log level
logsnap --level ERROR app.log

# Pattern search with context lines
logsnap --pattern "timeout" -C 2 app.log

# Filter by time range
logsnap --from "2024-01-15 14:00" --to "2024-01-15 15:00" app.log

# Pipe from anywhere
kubectl logs pod/api | logsnap --level ERROR
journalctl | logsnap --summary

# Follow live logs
logsnap --follow --level ERROR app.log
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
python -m pytest --cov=logsnap
```

## License

MIT — see [LICENSE](LICENSE)
