# Check Timestamp Tool - Implementation Plan

## Purpose

Validate that the `timeUnixNano` field in OTLP log records falls within a user-specified time range. This helps filter and validate log data based on timestamp bounds.

## Tool Name

**CLI Command**: `otlp-check-timestamp`  
**Module**: `src/otlp_analyzer/tools/check_timestamp.py`

## Behavior

### Input

- Read JSONL from **stdin** line by line
- Each line contains one OTLP JSON object
- Each object may contain multiple log records in the structure:
  - `resourceLogs[i].scopeLogs[j].logRecords[k]`

### Processing

For each JSON line:

1. Parse the OTLP structure
2. Extract all log records (potentially multiple per line)
3. For each log record:
   - Extract `timeUnixNano` (convert string to int64 nanoseconds)
   - Compare against the user-specified time range
   - Record the result (in range, out of range, or error)

### Output

**Default behavior** (only show problems):

- Output **only** for log records with mismatches or errors
- Include line number, record position, and details
- Human-readable format

**Verbose mode** (`--verbose`, `-v`):

- Show all log records (matches and mismatches)

**Quiet mode** (`--quiet`, `-q`):

- Only show summary counts at the end

### Exit Codes

- `0`: All timestamps matched (or no log records found)
- `1`: One or more mismatches or errors detected

## Output Format

### Default (out of range only)

```
Line 1, Record 0: OUT OF RANGE (too early)
  timeUnixNano:    2019-12-15T10:30:00.000Z (1576408200000000000)
  expected range:  2020-01-01T00:00:00.000Z - 2020-12-31T23:59:59.999Z
  difference:      -16 days, 13:30:00 before start

Line 5, Record 2: OUT OF RANGE (too late)
  timeUnixNano:    2021-03-15T14:25:30.123Z (1615819530123000000)
  expected range:  2020-01-01T00:00:00.000Z - 2020-12-31T23:59:59.999Z
  difference:      73 days, 14:25:30.123 after end

Line 8, Record 0: ERROR - Missing timeUnixNano field

---
Summary:
  Total lines processed: 10
  Total log records: 42
  In range: 38
  Out of range (too early): 1
  Out of range (too late): 1
  Errors: 2
```

### Verbose Mode

```
Line 1, Record 0: OUT OF RANGE (too early)
  timeUnixNano:    2019-12-15T10:30:00.000Z (1576408200000000000)
  expected range:  2020-01-01T00:00:00.000Z - 2020-12-31T23:59:59.999Z
  difference:      -16 days, 13:30:00 before start

Line 1, Record 1: IN RANGE
  timeUnixNano:    2020-06-15T12:00:00.000Z (1592222400000000000)
  expected range:  2020-01-01T00:00:00.000Z - 2020-12-31T23:59:59.999Z

Line 2, Record 0: IN RANGE
  ...

---
Summary: (same as above)
```

### Quiet Mode

````
In range: 38, Out of range: 2, Errors: 2
```## CLI Interface

```bash
otlp-check-timestamp --start START --end END [OPTIONS]

Arguments:
  --start TEXT  Start of time range (required)
                Formats: ISO 8601, Unix timestamp, relative (e.g., "2020-01-01", "2020-01-01T00:00:00Z", "1577836800")
  --end TEXT    End of time range (required)
                Formats: same as --start

Options:
  -v, --verbose  Show all log records (in range and out of range)
  -q, --quiet    Only show summary counts
  -h, --help     Show this message and exit

Examples:
  cat logs.jsonl | otlp-check-timestamp --start 2020-01-01 --end 2020-12-31
  cat logs.jsonl | otlp-check-timestamp --start 2020-01-01T00:00:00Z --end 2020-12-31T23:59:59Z
  cat logs.jsonl | otlp-check-timestamp --start 1577836800 --end 1609459199 --verbose
  otlp-check-timestamp --start "2020-01-01" --end "2020-12-31" < logs.jsonl
````

## Implementation Approach

### Main Logic Flow

1. **Parse CLI arguments**: Extract and validate start/end time range from user input

   - Parse start and end timestamps using the timestamp parser
   - Validate that start < end
   - Exit with code 2 if arguments are invalid

2. **Initialize tracking**: Set up counters for in_range, too_early, too_late, and errors

3. **Process input stream**: Read JSONL from stdin line by line

   - Parse each line as OTLP JSON structure
   - Extract all log records from nested arrays
   - Handle JSON parsing errors gracefully

4. **Check each log record**:

   - Extract `timeUnixNano` field
   - Compare against time range bounds
   - Classify as: in range, too early, too late, or error
   - Store result for output

5. **Generate output**: Based on verbosity flags

   - Default: Show only out-of-range and error records
   - Verbose: Show all records
   - Quiet: Show only summary counts

6. **Exit**: Return appropriate exit code based on results

### Timestamp Range Checking

- **In range**: `start_nano <= timeUnixNano <= end_nano`
- **Too early**: `timeUnixNano < start_nano`
- **Too late**: `timeUnixNano > end_nano`
- Range bounds are inclusive on both ends

### Error Handling

**Types of errors to report**:

1. **JSON parse error**: Entire line is invalid JSON

   ```
   Line 5: ERROR - Invalid JSON
     error: Expecting property name enclosed in double quotes: line 1 column 2
   ```

2. **Missing `timeUnixNano`**: Field not present or not parseable

   ```
   Line 3, Record 1: ERROR - Missing or invalid timeUnixNano field
   ```

3. **Invalid time range arguments**: Start/end timestamps cannot be parsed or start >= end
   ```
   Error parsing time range: Could not parse timestamp "invalid-date"
   Error: start time must be before end time
   ```
   Exit code: 2 (to distinguish from validation failures)

### Edge Cases

- **Empty JSONL line**: Skip silently
- **Empty arrays**: `resourceLogs`, `scopeLogs`, or `logRecords` is empty → no records to check
- **Exactly at boundary**: Timestamps exactly equal to start or end are considered **in range** (inclusive bounds)
- **Timezone handling**: Convert all timestamps to UTC nanoseconds for comparison
- **Various input formats**: Support ISO 8601, Unix timestamps (auto-detect seconds/milliseconds/nanoseconds)
- **Very large differences**: Format as days/hours/minutes (e.g., "248 days, 8:28:56")

## Test Cases

**Test data needed**:

- Log records with timestamps in range (mid-range)
- Log records with timestamps too early (before start)
- Log records with timestamps too late (after end)
- Log records with timestamps exactly at start boundary
- Log records with timestamps exactly at end boundary
- JSON lines with multiple log records (mixed in/out of range)
- Log records missing `timeUnixNano` field
- Log records with invalid `timeUnixNano` values (non-numeric)
- Invalid JSON lines
- Empty arrays (no log records)

**Test scenarios**:

1. Timestamp in range
2. Timestamp too early (before start)
3. Timestamp too late (after end)
4. Timestamp exactly at start boundary (should be in range)
5. Timestamp exactly at end boundary (should be in range)
6. Multiple records per line (mixed: in/out of range)
7. Missing `timeUnixNano` field
8. Invalid `timeUnixNano` value (not a number)
9. Invalid JSON line
10. Empty arrays (no log records)
11. Various input formats for --start and --end (ISO 8601, Unix timestamps)
12. Invalid time range (start >= end)
13. Unparseable --start or --end arguments

## Integration with Common Modules

### Dependencies

```python
from otlp_analyzer.common.otlp_parser import parse_otlp_line, LogRecord
from otlp_analyzer.common.timestamp_parser import extract_and_parse_timestamp
from otlp_analyzer.common.utils import (
    timestamps_match,
    format_timestamp,
    format_difference,
)
```

### Expected APIs

**`otlp_parser.parse_otlp_line(line: str) -> list[LogRecord]`**

## Integration with Common Modules

### Dependencies on Common Modules

**OTLP Parser**:

- Parse JSONL and extract log records from OTLP structure
- Navigate nested arrays: `resourceLogs[*].scopeLogs[*].logRecords[*]`
- Extract `timeUnixNano` field (convert string to int64 nanoseconds)
- Handle missing/malformed fields gracefully

**Timestamp Parser**:

- Parse timestamp strings in various formats
- Support ISO 8601 variants (with/without time, with/without milliseconds)
- Support Unix timestamps (auto-detect seconds/milliseconds/nanoseconds)
- Convert all timestamps to nanoseconds for uniform comparison
- Raise appropriate exceptions for unparseable input

**Utilities**:

- Format timestamps as human-readable ISO 8601 strings
- Format time differences as human-readable durations (days, hours, minutes, seconds)
- Used for displaying timestamps and differences in output
