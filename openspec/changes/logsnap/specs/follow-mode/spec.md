## ADDED Requirements

### Requirement: Live-tail a growing log file
The system SHALL support streaming new lines appended to a file in real time via `--follow`, applying all active filters to each new line.

#### Scenario: Follow mode streams new lines
- **WHEN** the user runs `logsnap --follow app.log`
- **THEN** the tool SHALL print any new lines (that pass active filters) as they are appended to the file

#### Scenario: Follow mode with filters
- **WHEN** the user runs `logsnap --follow --level ERROR app.log`
- **THEN** only new ERROR lines SHALL be printed in real time

#### Scenario: Follow mode exits on Ctrl+C
- **WHEN** the user presses Ctrl+C while in follow mode
- **THEN** the tool SHALL exit cleanly with exit code 0

### Requirement: Handle log file rotation in follow mode
The system SHALL detect when a followed file is rotated (size decreases) and re-open it from the beginning.

#### Scenario: File shrinks (rotation detected)
- **WHEN** the file's current size is less than the last known read position
- **THEN** the tool SHALL seek to position 0 and resume reading from the new file start

### Requirement: Follow mode prints existing content first
By default, `--follow` SHALL first print the last 10 lines of the existing file (that pass filters) before streaming new content.

#### Scenario: Tail existing content before following
- **WHEN** the user starts `--follow` on an existing file
- **THEN** up to the last 10 matching lines SHALL be printed before live-streaming begins
