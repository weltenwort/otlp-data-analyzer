"""Parse timestamps from various string formats and convert to nanoseconds."""

import re
from datetime import datetime, timezone
from typing import Union


class TimestampParseError(Exception):
    """Raised when a timestamp cannot be parsed."""


def parse_timestamp(timestamp_str: str) -> int:
    """
    Parse a timestamp string and return nanoseconds since Unix epoch.

    Supported formats:
    - ISO 8601: 2020-01-01, 2020-01-01T00:00:00, 2020-01-01T00:00:00Z,
                2020-01-01T00:00:00.123Z, 2020-01-01T00:00:00+00:00
    - Unix timestamps: Auto-detect seconds, milliseconds, or nanoseconds
                      based on magnitude

    Args:
        timestamp_str: The timestamp string to parse

    Returns:
        Timestamp in nanoseconds since Unix epoch

    Raises:
        TimestampParseError: If the timestamp cannot be parsed
    """
    timestamp_str = timestamp_str.strip()

    # Try to parse as a number (Unix timestamp)
    try:
        # Try as integer first to avoid floating point precision issues
        timestamp_num: Union[int, float]
        if "." not in timestamp_str:
            timestamp_num = int(timestamp_str)
        else:
            timestamp_num = float(timestamp_str)
        return _parse_unix_timestamp(timestamp_num)
    except ValueError:
        pass

    # Try to parse as ISO 8601
    try:
        return _parse_iso8601(timestamp_str)
    except ValueError as e:
        raise TimestampParseError(
            f"Could not parse timestamp '{timestamp_str}': {e}"
        ) from e


def _parse_unix_timestamp(timestamp: Union[int, float]) -> int:
    """
    Parse a Unix timestamp and convert to nanoseconds.

    Auto-detects whether the input is in seconds, milliseconds, or nanoseconds
    based on magnitude.

    Args:
        timestamp: Unix timestamp as int or float

    Returns:
        Timestamp in nanoseconds
    """
    # Determine unit based on magnitude
    # Timestamps before year 2300 in seconds: < 10^10
    # Timestamps before year 2300 in milliseconds: < 10^13
    # Timestamps in nanoseconds: >= 10^18

    # Use integer comparisons to avoid float conversion
    if timestamp < 10_000_000_000:  # 10^10
        # Seconds
        if isinstance(timestamp, int):
            return timestamp * 1_000_000_000
        return round(timestamp * 1e9)
    if timestamp < 10_000_000_000_000:  # 10^13
        # Milliseconds
        if isinstance(timestamp, int):
            return timestamp * 1_000_000
        return round(timestamp * 1e6)
    # Nanoseconds
    return round(timestamp)


def _parse_iso8601(timestamp_str: str) -> int:
    """
    Parse an ISO 8601 timestamp string and convert to nanoseconds.

    Supports various ISO 8601 formats with and without time components.

    Args:
        timestamp_str: ISO 8601 timestamp string

    Returns:
        Timestamp in nanoseconds

    Raises:
        ValueError: If the timestamp cannot be parsed
    """
    # Handle date-only format (YYYY-MM-DD)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", timestamp_str):
        timestamp_str += "T00:00:00Z"

    # Handle format without timezone (assume UTC)
    if (
        "T" in timestamp_str
        and not any(timestamp_str.endswith(tz) for tz in ["Z", "+00:00", "-00:00"])
        and not re.search(r"[+-]\d{2}:\d{2}$", timestamp_str)
    ):
        timestamp_str += "Z"

    # Parse the datetime
    # Try with fractional seconds first
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]:
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            # Ensure timezone-aware (assume UTC if naive)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            # Convert to nanoseconds - use round to avoid floating point precision issues
            return round(dt.timestamp() * 1e9)
        except ValueError:
            continue

    raise ValueError(f"Unsupported ISO 8601 format: {timestamp_str}")
