## ADDED Requirements

### Requirement: Filter by log level
The system SHALL support filtering lines to one or more severity levels via `--level`.

#### Scenario: Single level filter
- **WHEN** the user passes `--level ERROR`
- **THEN** only lines with level=ERROR SHALL be output

#### Scenario: Multiple level filter
- **WHEN** the user passes `--level ERROR --level WARN`
- **THEN** lines with level=ERROR or level=WARN SHALL be output

#### Scenario: Case-insensitive level matching
- **WHEN** the user passes `--level error` (lowercase)
- **THEN** it SHALL match the same as `--level ERROR`

#### Scenario: No level filter
- **WHEN** no `--level` flag is provided
- **THEN** lines of all levels SHALL pass the level filter

### Requirement: Filter by regex or keyword pattern
The system SHALL support filtering lines whose message matches a keyword or regular expression via `--pattern`.

#### Scenario: Keyword match
- **WHEN** the user passes `--pattern "connection refused"`
- **THEN** only lines containing that substring SHALL be output

#### Scenario: Regex match
- **WHEN** the user passes `--pattern "user_id=\d+"` (a valid regex)
- **THEN** only lines matching the regex SHALL be output

#### Scenario: Invalid regex
- **WHEN** the user passes an invalid regex pattern
- **THEN** the tool SHALL print a clear error message and exit with a non-zero code

### Requirement: Filter by time range
The system SHALL support filtering lines to a time window via `--from` and `--to` flags.

#### Scenario: From-only filter
- **WHEN** the user passes `--from "2024-01-15 14:00:00"`
- **THEN** only lines with timestamp >= that value SHALL be output

#### Scenario: To-only filter
- **WHEN** the user passes `--to "2024-01-15 15:00:00"`
- **THEN** only lines with timestamp <= that value SHALL be output

#### Scenario: Lines with no timestamp under time filter
- **WHEN** a time filter is active and a line has no parsed timestamp
- **THEN** that line SHALL be excluded from output

### Requirement: Filters compose with AND logic
When multiple filters are active, a line SHALL only be output if it passes ALL active filters.

#### Scenario: Level AND pattern filter
- **WHEN** both `--level ERROR` and `--pattern "timeout"` are active
- **THEN** only lines that are both level=ERROR AND match "timeout" SHALL be output
