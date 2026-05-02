## ADDED Requirements

### Requirement: Stream large files without loading into memory
The system SHALL read log files line-by-line using a generator, keeping memory usage below 50 MB RSS regardless of file size.

#### Scenario: Processing a 5 GB file
- **WHEN** the user runs `logsnap` on a 5 GB log file
- **THEN** memory usage SHALL remain below 50 MB RSS throughout processing

#### Scenario: Processing via stdin
- **WHEN** the user pipes log content into `logsnap` via stdin
- **THEN** the tool SHALL read from stdin line-by-line without buffering the full stream

### Requirement: First result latency
The system SHALL yield the first matching output line within 3 seconds of startup on a 1 GB file.

#### Scenario: Fast first result
- **WHEN** a user runs a filtered query on a 1 GB log file
- **THEN** the first matching line SHALL appear in the terminal within 3 seconds

### Requirement: Accept file path or stdin
The system SHALL accept either a positional file path argument or read from stdin when no file is given.

#### Scenario: File path argument
- **WHEN** the user provides a file path as a positional argument
- **THEN** the tool SHALL open and stream that file

#### Scenario: Stdin fallback
- **WHEN** no file path is provided and stdin is a pipe
- **THEN** the tool SHALL read from stdin

#### Scenario: No input and no stdin
- **WHEN** no file path is provided and stdin is a TTY
- **THEN** the tool SHALL print an error and exit with a non-zero code
