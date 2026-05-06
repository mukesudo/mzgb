## ADDED Requirements

### Requirement: Show lines before and after a match
The system SHALL support showing N lines before and after each matching line via `-C / --context N`.

#### Scenario: Context lines displayed
- **WHEN** the user passes `-C 3` and a line matches
- **THEN** the 3 lines before the match and 3 lines after SHALL also be printed, visually separated from other matches

#### Scenario: Context separator between match groups
- **WHEN** two match groups are non-adjacent (their context windows do not overlap)
- **THEN** a `--` separator SHALL be printed between them

#### Scenario: Overlapping context groups merged
- **WHEN** two matches are close enough that their context windows overlap
- **THEN** the overlapping lines SHALL be shown once (no duplication) and no separator SHALL be inserted

#### Scenario: Context at start of file
- **WHEN** a match occurs near the beginning of the file and fewer than N pre-context lines exist
- **THEN** only the available preceding lines SHALL be shown (no error)

### Requirement: Context does not affect filter logic
Lines shown as context SHALL NOT be required to pass the active filters — they are shown as surrounding raw text.

#### Scenario: Context line does not match filter
- **WHEN** a context line does not match the active level or pattern filter
- **THEN** it SHALL still be printed as context and SHALL be visually distinguished (dimmed)
