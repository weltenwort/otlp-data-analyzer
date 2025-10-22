"""Utility functions for formatting timestamps and time differences."""

from datetime import datetime, timezone


def format_timestamp(timestamp_ns: int) -> str:
    """
    Format a timestamp in nanoseconds as an ISO 8601 string.

    Args:
        timestamp_ns: Timestamp in nanoseconds since Unix epoch

    Returns:
        ISO 8601 formatted string (e.g., "2020-01-01T00:00:00.000Z")
    """
    timestamp_s = timestamp_ns / 1e9
    dt = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
    # Format with milliseconds
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def format_difference(difference_ns: int, reference: str = "") -> str:
    """
    Format a time difference in nanoseconds as a human-readable string.

    Args:
        difference_ns: Time difference in nanoseconds (can be negative)
        reference: Reference point (e.g., "before start", "after end")

    Returns:
        Human-readable duration string
    """
    abs_diff_ns = abs(difference_ns)

    # Convert to seconds and extract components
    total_seconds = abs_diff_ns / 1e9
    days = int(total_seconds // 86400)
    remaining_seconds = total_seconds % 86400
    hours = int(remaining_seconds // 3600)
    remaining_seconds %= 3600
    minutes = int(remaining_seconds // 60)
    seconds = remaining_seconds % 60

    # Format the duration
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")

    time_str = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    parts.append(time_str)

    duration = ", ".join(parts)

    # Add reference if provided
    if reference:
        return f"{duration} {reference}"
    return duration
