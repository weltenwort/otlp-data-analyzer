"""Parse OTLP JSON structure and extract log records."""

import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class LogRecord:
    """Represents a single OTLP log record with its position."""

    time_unix_nano: Optional[int]
    line_number: int
    record_index: int
    raw_data: dict[str, Any]


class OTLPParseError(Exception):
    """Raised when OTLP JSON structure cannot be parsed."""


def parse_otlp_line(line: str, line_number: int) -> list[LogRecord]:
    """
    Parse a single line of OTLP JSONL and extract all log records.

    The OTLP structure is:
    resourceLogs[i].scopeLogs[j].logRecords[k]

    Args:
        line: A single line of JSONL containing OTLP data
        line_number: Line number in the input (for error reporting)

    Returns:
        List of LogRecord objects extracted from the line

    Raises:
        OTLPParseError: If the JSON is invalid or doesn't match expected structure
    """
    # Skip empty lines
    if not line.strip():
        return []

    # Parse JSON
    try:
        data = json.loads(line)
    except json.JSONDecodeError as e:
        raise OTLPParseError(f"Invalid JSON: {e}") from e

    # Extract log records from nested structure
    log_records: list[LogRecord] = []
    record_index = 0

    # Navigate: resourceLogs[*].scopeLogs[*].logRecords[*]
    resource_logs = data.get("resourceLogs", [])
    if not isinstance(resource_logs, list):
        raise OTLPParseError("resourceLogs must be a list")

    for resource_log in resource_logs:
        if not isinstance(resource_log, dict):
            continue

        scope_logs = resource_log.get("scopeLogs", [])
        if not isinstance(scope_logs, list):
            continue

        for scope_log in scope_logs:
            if not isinstance(scope_log, dict):
                continue

            log_records_list = scope_log.get("logRecords", [])
            if not isinstance(log_records_list, list):
                continue

            for log_record_data in log_records_list:
                if not isinstance(log_record_data, dict):
                    continue

                # Extract timeUnixNano
                time_unix_nano = _extract_time_unix_nano(log_record_data)

                log_records.append(
                    LogRecord(
                        time_unix_nano=time_unix_nano,
                        line_number=line_number,
                        record_index=record_index,
                        raw_data=log_record_data,
                    )
                )
                record_index += 1

    return log_records


def _extract_time_unix_nano(log_record: dict[str, Any]) -> Optional[int]:
    """
    Extract and convert timeUnixNano from a log record.

    The field can be a string or an integer representing nanoseconds.

    Args:
        log_record: The log record dictionary

    Returns:
        Timestamp in nanoseconds, or None if field is missing or invalid
    """
    time_value = log_record.get("timeUnixNano")
    if time_value is None:
        return None

    try:
        # Handle both string and integer formats
        if isinstance(time_value, str):
            return int(time_value)
        if isinstance(time_value, int):
            return time_value
        return None
    except (ValueError, TypeError):
        return None
