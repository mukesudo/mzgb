## ADDED Requirements

### Requirement: Auto-detect log format
The system SHALL sample the first 20 non-empty lines of input to detect the log format (JSON, logfmt, or plain-text) and lock in the parser for the remainder of the file.

#### Scenario: JSON log file detected
- **WHEN** the first 20 lines are valid JSON objects with a `level` or `severity` field
- **THEN** the JSON parser SHALL be selected and used for all subsequent lines

#### Scenario: Logfmt file detected
- **WHEN** the first 20 lines match `key=value` logfmt pattern with a `level=` field
- **THEN** the logfmt parser SHALL be selected

#### Scenario: Plain-text fallback
- **WHEN** format detection is ambiguous or no structured format is found
- **THEN** the plain-text parser SHALL be used as the default

### Requirement: Parse structured fields from each line
The parser SHALL extract `timestamp`, `level`, `message`, and `extras` from each log line into a structured object.

#### Scenario: Plain-text line with leading level
- **WHEN** a line matches `LEVEL: message` or `[LEVEL] message` or `LEVEL message` pattern
- **THEN** the parser SHALL extract level and message; timestamp SHALL be None if not present

#### Scenario: JSON line parsing
- **WHEN** a JSON line contains `level`/`severity` and `message`/`msg` fields
- **THEN** both fields SHALL be extracted; common timestamp keys (`time`, `timestamp`, `ts`) SHALL also be extracted

#### Scenario: Malformed or unparseable line
- **WHEN** a line cannot be parsed by the selected parser
- **THEN** the system SHALL treat the line as raw text with level=UNKNOWN and SHALL NOT crash

### Requirement: Timestamp normalization
The system SHALL normalize detected timestamps to `datetime` objects, supporting ISO 8601, Unix epoch, and common syslog formats.

#### Scenario: ISO 8601 timestamp
- **WHEN** a line contains a timestamp like `2024-01-15T14:32:01Z` or `2024-01-15 14:32:01`
- **THEN** it SHALL be parsed into a timezone-aware or naive datetime object

#### Scenario: Unknown timestamp format
- **WHEN** a timestamp cannot be parsed
- **THEN** the field SHALL be set to None and processing SHALL continue normally
