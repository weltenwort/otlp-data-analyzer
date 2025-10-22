# OTLP Data Analyzer

A collection of Python CLI tools to analyze JSONL files in the OTLP (OpenTelemetry Protocol) JSON format.

## Features

- **otlp-check-timestamp**: Validate that `timeUnixNano` fields in OTLP log records fall within a specified time range

## Installation

### Using Nix (Recommended)

```bash
# Enter the development environment
nix develop

# Install the package in development mode
uv pip install -e .
```

### Using pip

```bash
# Create a virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install the package
pip install -e .
```

## Usage

### otlp-check-timestamp

Validate timestamps in OTLP log records against a time range.

```bash
# Basic usage
cat logs.jsonl | otlp-check-timestamp --start 2020-01-01 --end 2020-12-31

# With ISO 8601 timestamps
cat logs.jsonl | otlp-check-timestamp --start 2020-01-01T00:00:00Z --end 2020-12-31T23:59:59Z

# With Unix timestamps
cat logs.jsonl | otlp-check-timestamp --start 1577836800 --end 1609459199

# Verbose mode (show all records)
cat logs.jsonl | otlp-check-timestamp --start 2020-01-01 --end 2020-12-31 --verbose

# Quiet mode (only show summary)
cat logs.jsonl | otlp-check-timestamp --start 2020-01-01 --end 2020-12-31 --quiet

# Using input redirection
otlp-check-timestamp --start "2020-01-01" --end "2020-12-31" < logs.jsonl
```

**Exit codes:**

- `0`: All timestamps are within range
- `1`: One or more timestamps are out of range or errors occurred
- `2`: Invalid arguments (unparseable timestamps or invalid range)

## Development

### Setup

```bash
# Enter the Nix development environment
nix develop

# Install in development mode with dev dependencies
uv pip install -e ".[dev]"
```

### Code Quality

```bash
# Format code
black src/

# Type check
mypy src/

# Lint
pylint src/

# Run tests
python -m pytest src/
```

### Project Structure

```
otlp-data-analyzer/
├── src/
│   └── otlp_analyzer/
│       ├── common/              # Shared code
│       │   ├── otlp_parser.py
│       │   ├── timestamp_parser.py
│       │   └── utils.py
│       └── tools/               # CLI tools
│           └── check_timestamp.py
└── tests/                       # Test data files
```

## License

MIT
