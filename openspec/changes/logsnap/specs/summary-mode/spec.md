## ADDED Requirements

### Requirement: Produce a summary table instead of raw lines
The system SHALL support a `--summary` flag that, instead of printing matched lines, prints a table of match counts grouped by log level.

#### Scenario: Summary table output
- **WHEN** the user runs `logsnap --summary app.log`
- **THEN** a table SHALL be printed showing each level and the count of matched lines for that level

#### Scenario: Summary respects active filters
- **WHEN** `--summary` is combined with `--level` or `--pattern`
- **THEN** the counts SHALL reflect only the lines that passed those filters

### Requirement: Top recurring patterns in summary
The system SHALL include the top 5 most frequent normalized message patterns in the summary output.

#### Scenario: Top patterns shown
- **WHEN** `--summary` is run on a file
- **THEN** the output SHALL include a second table listing the top 5 message patterns by frequency, with their count

#### Scenario: Fewer than 5 distinct patterns
- **WHEN** the file contains fewer than 5 distinct message patterns
- **THEN** only the available patterns SHALL be shown (no error, no padding)

### Requirement: Summary exits with non-zero code when errors found
The system SHALL exit with code 1 if the summary contains any ERROR or FATAL level lines.

#### Scenario: Errors present in summary
- **WHEN** the summary contains at least one ERROR or FATAL line
- **THEN** the exit code SHALL be 1, enabling use in CI/CD scripts
