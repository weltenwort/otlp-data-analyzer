"""Tests for utils module."""

from otlp_analyzer.common.utils import format_difference, format_timestamp


class TestFormatTimestamp:
    """Test timestamp formatting."""

    def test_format_basic_timestamp(self) -> None:
        """Test formatting a basic timestamp."""
        # 2020-01-01T00:00:00.000Z
        timestamp_ns = 1577836800000000000
        result = format_timestamp(timestamp_ns)
        assert result == "2020-01-01T00:00:00.000Z"

    def test_format_timestamp_with_milliseconds(self) -> None:
        """Test formatting a timestamp with milliseconds."""
        # 2020-06-15T12:30:45.123Z
        timestamp_ns = 1592224245123000000
        result = format_timestamp(timestamp_ns)
        assert result == "2020-06-15T12:30:45.123Z"

    def test_format_timestamp_with_time(self) -> None:
        """Test formatting a timestamp with time component."""
        # 2020-12-31T23:59:59.999Z
        timestamp_ns = 1609459199999000000
        result = format_timestamp(timestamp_ns)
        assert result == "2020-12-31T23:59:59.999Z"


class TestFormatDifference:
    """Test time difference formatting."""

    def test_format_seconds_only(self) -> None:
        """Test formatting difference with only seconds."""
        # 45.5 seconds
        diff_ns = 45500000000
        result = format_difference(diff_ns)
        assert "00:00:45.500" in result

    def test_format_minutes_and_seconds(self) -> None:
        """Test formatting difference with minutes and seconds."""
        # 5 minutes, 30 seconds
        diff_ns = 330000000000
        result = format_difference(diff_ns)
        assert "00:05:30.000" in result

    def test_format_hours_minutes_seconds(self) -> None:
        """Test formatting difference with hours, minutes, and seconds."""
        # 2 hours, 15 minutes, 30 seconds
        diff_ns = 8130000000000
        result = format_difference(diff_ns)
        assert "02:15:30.000" in result

    def test_format_days(self) -> None:
        """Test formatting difference with days."""
        # 16 days, 13 hours, 30 minutes
        diff_ns = 1431000000000000
        result = format_difference(diff_ns)
        assert "16 days" in result
        assert "13:30:00" in result

    def test_format_single_day(self) -> None:
        """Test formatting difference with single day (singular)."""
        # 1 day exactly
        diff_ns = 86400000000000
        result = format_difference(diff_ns)
        assert "1 day" in result
        assert "1 days" not in result

    def test_format_with_reference(self) -> None:
        """Test formatting difference with reference point."""
        # 5 minutes before start
        diff_ns = 300000000000
        result = format_difference(diff_ns, "before start")
        assert "before start" in result

    def test_format_negative_difference(self) -> None:
        """Test formatting negative difference."""
        # -10 minutes
        diff_ns = -600000000000
        result = format_difference(diff_ns, "after end")
        assert "00:10:00" in result

    def test_format_large_difference(self) -> None:
        """Test formatting very large difference."""
        # 73 days, 14 hours, 25 minutes, 30.123 seconds
        diff_ns = 6359130123000000
        result = format_difference(diff_ns)
        assert "73 days" in result
        assert "14:25:30.123" in result
