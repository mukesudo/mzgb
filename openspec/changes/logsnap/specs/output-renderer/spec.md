## ADDED Requirements

### Requirement: Color-coded output per log level
The system SHALL render log level labels with distinct colors in terminal output.

#### Scenario: Level colors in TTY
- **WHEN** stdout is a TTY
- **THEN** ERROR/FATAL SHALL render in red, WARN in yellow, INFO in green, DEBUG in dim/grey

#### Scenario: No color when piping
- **WHEN** stdout is not a TTY (piped to a file or another process)
- **THEN** output SHALL be plain text with no ANSI escape codes

### Requirement: Highlight matched pattern in output
The system SHALL highlight the portion of each line that matched `--pattern` when in TTY mode.

#### Scenario: Match highlighted
- **WHEN** a line matches `--pattern "timeout"` and stdout is a TTY
- **THEN** the word "timeout" SHALL be visually highlighted (bold or underlined) within the line

### Requirement: Dim timestamps and context lines
The system SHALL render timestamps in a dimmed style to reduce visual noise, and context lines SHALL be visually distinct from matched lines.

#### Scenario: Timestamp dimmed
- **WHEN** a parsed timestamp is present in a line
- **THEN** the timestamp portion SHALL be rendered dim/grey in TTY output

#### Scenario: Context lines visually distinguished
- **WHEN** context lines are shown alongside a match
- **THEN** context lines SHALL be rendered in a dimmer or muted style compared to the match line

### Requirement: Accessible help text
The tool SHALL provide `--help` output that allows a new user to run a useful query within 2 minutes of first install.

#### Scenario: Help shows examples
- **WHEN** the user runs `logsnap --help`
- **THEN** the help output SHALL include at least 3 concrete usage examples covering the most common flags

### Requirement: Graceful error handling
The system SHALL handle malformed lines, binary content, and permission errors without crashing, printing a warning to stderr and continuing.

#### Scenario: Permission denied
- **WHEN** the file cannot be opened due to a permission error
- **THEN** the tool SHALL print a clear error to stderr and exit with a non-zero code

#### Scenario: Binary or non-UTF-8 content
- **WHEN** a line contains non-UTF-8 bytes
- **THEN** the line SHALL be decoded with error replacement (not crash) and a warning SHALL be printed to stderr
