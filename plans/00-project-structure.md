# OTLP Data Analyzer - Project Structure Plan

## Overview

A collection of Python CLI tools to analyze JSONL files in the OTLP (OpenTelemetry Protocol) JSON format. The tools share common code for parsing and validation, with a focus on OTLP logs.

## Project Structure

```
otlp-data-analyzer/
├── flake.nix                    # Nix development environment (existing)
├── pyproject.toml               # Project metadata, dependencies, CLI entry points
├── README.md                    # Project documentation and usage
├── .gitignore                   # Git ignore patterns
├── plans/                       # Planning documents
│   ├── 00-project-structure.md  # This file
│   └── 01-check-timestamp.md    # First tool specification
└── src/
    └── otlp_analyzer/
        ├── __init__.py
        ├── common/              # Shared code for all tools
        │   ├── __init__.py
        │   ├── otlp_parser.py
        │   ├── otlp_parser_test.py
        │   ├── timestamp_parser.py
        │   ├── timestamp_parser_test.py
        │   ├── utils.py
        │   └── utils_test.py
        └── tools/               # Individual CLI tools
            ├── __init__.py
            ├── check_timestamp.py
            └── check_timestamp_test.py
```

## Common Modules

### `otlp_parser.py`

**Purpose**: Parse OTLP JSON structure and extract relevant fields

**Responsibilities**:

- Parse JSONL (one JSON object per line)
- Navigate OTLP log structure: `resourceLogs[*].scopeLogs[*].logRecords[*]`
- Extract fields from log records:
  - `timeUnixNano` (string → int64 nanoseconds)
  - Other fields as needed for future tools
- Handle nested arrays (multiple resources, scopes, and log records per line)
- Gracefully handle missing/malformed fields
- Return structured data for processing

### `timestamp_parser.py`

**Purpose**: Parse timestamps from various string formats

**Responsibilities**:

- Parse timestamp strings provided as CLI arguments or in data fields
- Support multiple timestamp formats:
  - ISO 8601 variants (with/without time component, with/without milliseconds, with/without timezone)
  - Unix timestamps (auto-detect seconds, milliseconds, or nanoseconds based on magnitude)
- Return timestamps normalized to nanoseconds
- Handle parsing failures with appropriate exceptions
- Auto-detect format based on input structure

### `utils.py`

**Purpose**: Utility functions used across tools

**Responsibilities**:

- Nanosecond ↔ human-readable conversions
- Time difference formatting (convert nanoseconds to days/hours/minutes/seconds)
- Error formatting helpers
- Common constants

## Tool Structure

Each tool in `src/otlp_analyzer/tools/` should:

- Use click for CLI argument parsing
- Import and use common modules for shared functionality
- Provide standard verbosity options (--verbose, --quiet)
- Read from stdin for processing JSONL data
- Output human-readable results by default
- Exit with appropriate status codes

## Dependencies

### Required

- **click**: CLI framework for parsing arguments and options
- Python 3.13+ (stdlib for everything else)

### Development

- **black**: Code formatting
- **mypy**: Type checking
- **pylint**: Linting
- **pytest** (implicit): Test runner (via co-located tests)

## Configuration (`pyproject.toml`)

**Project Configuration**:

- Package name: `otlp-analyzer`
- Minimum Python version: 3.13

**CLI Entry Points**:

- Each tool gets a dedicated CLI command (e.g., `otlp-check-timestamp`)
- Entry points map command names to tool main functions

**Development Tool Configuration**:

- Black: Code formatting
- Mypy: Strict type checking
- Pylint: Linting

## Testing Strategy

### Co-located Tests

- Tests live in the same directory as the unit under test
- Named `<module>_test.py` (suffix pattern for better readability)
- Run with: `python -m pytest src/`

### Coverage Areas

- **Unit tests**: Each module's functionality in isolation
- **Integration tests**: End-to-end tool behavior with sample data
- **Edge cases**: Malformed JSON, missing fields, unusual timestamp formats

### Test Data

- Keep sample OTLP JSON lines in test files
- Include both valid and invalid examples
- Cover edge cases (empty arrays, missing fields, etc.)

## Installation & Usage

- Use uv for package management and installation
- Install in development mode for local development
- Tools become available as CLI commands after installation

### Usage Patterns

- Tools read JSONL from stdin
- Tools can be invoked by their CLI command name
- Alternative: Run as Python module
- Support for piping and redirection

```bash
# Use tools via installed CLI commands
cat logs.jsonl | otlp-check-timestamp
cat logs.jsonl | otlp-check-timestamp --verbose

# Or run as module
python -m otlp_analyzer.tools.check_timestamp < logs.jsonl
```

## Development Workflow

1. **Setup**: Enter Nix dev shell (automatic with direnv)
2. **Install**: `uv pip install -e .`
3. **Develop**: Write code with co-located tests
4. **Format**: `black src/`
5. **Type check**: `mypy src/`
6. **Lint**: `pylint src/`
7. **Test**: `python -m pytest src/`

## Future Extensions

Additional tools can be added to `src/otlp_analyzer/tools/` following the same pattern. Potential future tools:

- Validate timestamp consistency between `timeUnixNano` and `body.stringValue`
- Extract and analyze attributes
- Filter log records by criteria
- Validate OTLP schema compliance
- Statistical analysis of log data

Each tool will:

- Reuse common parsing code
- Provide a focused CLI interface
- Follow the same testing and documentation patterns
