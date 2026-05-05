# Changelog

## 0.1.0 (2026-05-05)

Initial public release.

### Features
- Filter by log level (`--level`, `-l`), repeatable
- Filter by keyword/regex pattern (`--pattern`, `-p`)
- Filter by time range (`--from`, `--to`)
- Context lines before/after matches (`--context`, `-C`)
- Follow mode — tail -f with filtering (`--follow`, `-f`)
- Summary mode — live stats table (`--summary`, `-s`)
- Live progress spinners on TTY for filter, context, and summary modes
- Format auto-detection: plaintext, JSON, logfmt
- Transparent `.gz` support
- Pipe support (`stdin`)
- ANSI color output with level coloring and pattern highlighting
- ASCII art banner on `--help`
- `--version` flag
