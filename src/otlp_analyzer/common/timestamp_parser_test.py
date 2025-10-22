"""Tests for timestamp_parser module."""

import pytest

from otlp_analyzer.common.timestamp_parser import (
    TimestampParseError,
    parse_timestamp,
)


class TestParseTimestamp:
    """Test timestamp parsing from various formats."""

    def test_parse_iso8601_date_only(self) -> None:
        """Test parsing date-only ISO 8601 format."""
        result = parse_timestamp("2020-01-01")
        # 2020-01-01T00:00:00Z in nanoseconds
        expected = 1577836800000000000
        assert result == expected

    def test_parse_iso8601_with_time(self) -> None:
        """Test parsing ISO 8601 with time component."""
        result = parse_timestamp("2020-06-15T12:30:45Z")
        # June 15, 2020, 12:30:45 UTC in nanoseconds
        expected = 1592224245000000000
        assert result == expected

    def test_parse_iso8601_with_milliseconds(self) -> None:
        """Test parsing ISO 8601 with milliseconds."""
        result = parse_timestamp("2020-06-15T12:30:45.123Z")
        expected = 1592224245123000000
        # Allow small floating point precision differences (within 1 microsecond)
        assert abs(result - expected) < 1000

    def test_parse_iso8601_with_timezone(self) -> None:
        """Test parsing ISO 8601 with timezone offset."""
        result = parse_timestamp("2020-06-15T12:30:45+00:00")
        expected = 1592224245000000000
        assert result == expected

    def test_parse_unix_seconds(self) -> None:
        """Test parsing Unix timestamp in seconds."""
        result = parse_timestamp("1577836800")
        # 2020-01-01T00:00:00Z
        expected = 1577836800000000000
        assert result == expected

    def test_parse_unix_milliseconds(self) -> None:
        """Test parsing Unix timestamp in milliseconds."""
        result = parse_timestamp("1577836800123")
        expected = 1577836800123000000
        # Integer strings should parse exactly
        assert result == expected

    def test_parse_unix_nanoseconds(self) -> None:
        """Test parsing Unix timestamp in nanoseconds."""
        result = parse_timestamp("1577836800123456789")
        expected = 1577836800123456789
        assert result == expected

    def test_parse_unix_float_seconds(self) -> None:
        """Test parsing Unix timestamp as float (seconds with decimals)."""
        result = parse_timestamp("1577836800.5")
        expected = 1577836800500000000
        assert result == expected

    def test_parse_invalid_format(self) -> None:
        """Test that invalid formats raise TimestampParseError."""
        with pytest.raises(TimestampParseError):
            parse_timestamp("not-a-timestamp")

    def test_parse_empty_string(self) -> None:
        """Test that empty string raises TimestampParseError."""
        with pytest.raises(TimestampParseError):
            parse_timestamp("")

    def test_parse_whitespace_handling(self) -> None:
        """Test that leading/trailing whitespace is handled."""
        result = parse_timestamp("  2020-01-01  ")
        expected = 1577836800000000000
        assert result == expected
