"""Tests for check_timestamp tool."""

import io

from otlp_analyzer.common.otlp_parser import LogRecord
from otlp_analyzer.tools.check_timestamp import (
    CheckResult,
    check_timestamp_range,
    format_result,
    format_summary,
    process_stream,
    Summary,
)


class TestCheckTimestampRange:
    """Test timestamp range checking logic."""

    def test_timestamp_in_range(self) -> None:
        """Test timestamp that's within range."""
        record = LogRecord(
            time_unix_nano=1592224245000000000,  # 2020-06-15
            line_number=1,
            record_index=0,
            raw_data={},
        )
        start_ns = 1577836800000000000  # 2020-01-01
        end_ns = 1609459199999000000  # 2020-12-31 23:59:59.999

        result = check_timestamp_range(record, start_ns, end_ns)

        assert result.status == "in_range"

    def test_timestamp_at_start_boundary(self) -> None:
        """Test timestamp exactly at start boundary."""
        record = LogRecord(
            time_unix_nano=1577836800000000000,
            line_number=1,
            record_index=0,
            raw_data={},
        )
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        result = check_timestamp_range(record, start_ns, end_ns)

        assert result.status == "in_range"

    def test_timestamp_at_end_boundary(self) -> None:
        """Test timestamp exactly at end boundary."""
        record = LogRecord(
            time_unix_nano=1609459199999000000,
            line_number=1,
            record_index=0,
            raw_data={},
        )
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        result = check_timestamp_range(record, start_ns, end_ns)

        assert result.status == "in_range"

    def test_timestamp_too_early(self) -> None:
        """Test timestamp before range."""
        record = LogRecord(
            time_unix_nano=1576408200000000000,  # 2019-12-15
            line_number=1,
            record_index=0,
            raw_data={},
        )
        start_ns = 1577836800000000000  # 2020-01-01
        end_ns = 1609459199999000000

        result = check_timestamp_range(record, start_ns, end_ns)

        assert result.status == "too_early"

    def test_timestamp_too_late(self) -> None:
        """Test timestamp after range."""
        record = LogRecord(
            time_unix_nano=1615819530123000000,  # 2021-03-15
            line_number=1,
            record_index=0,
            raw_data={},
        )
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        result = check_timestamp_range(record, start_ns, end_ns)

        assert result.status == "too_late"

    def test_missing_timestamp(self) -> None:
        """Test record with missing timeUnixNano."""
        record = LogRecord(
            time_unix_nano=None,
            line_number=1,
            record_index=0,
            raw_data={},
        )
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        result = check_timestamp_range(record, start_ns, end_ns)

        assert result.status == "error"
        assert "Missing or invalid" in result.error_message


class TestFormatResult:
    """Test result formatting."""

    def test_format_in_range(self) -> None:
        """Test formatting an in-range result."""
        record = LogRecord(
            time_unix_nano=1592224245000000000,
            line_number=5,
            record_index=2,
            raw_data={},
        )
        result = CheckResult(record=record, status="in_range")
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        output = format_result(result, start_ns, end_ns)

        assert "Line 5, Record 2: IN RANGE" in output

    def test_format_too_early(self) -> None:
        """Test formatting a too-early result."""
        record = LogRecord(
            time_unix_nano=1576408200000000000,
            line_number=1,
            record_index=0,
            raw_data={},
        )
        result = CheckResult(record=record, status="too_early")
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        output = format_result(result, start_ns, end_ns)

        assert "OUT OF RANGE (too early)" in output
        assert "timeUnixNano:" in output
        assert "expected range:" in output
        assert "difference:" in output
        assert "before start" in output

    def test_format_too_late(self) -> None:
        """Test formatting a too-late result."""
        record = LogRecord(
            time_unix_nano=1615819530123000000,
            line_number=5,
            record_index=2,
            raw_data={},
        )
        result = CheckResult(record=record, status="too_late")
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        output = format_result(result, start_ns, end_ns)

        assert "OUT OF RANGE (too late)" in output
        assert "after end" in output

    def test_format_error(self) -> None:
        """Test formatting an error result."""
        record = LogRecord(
            time_unix_nano=None,
            line_number=8,
            record_index=0,
            raw_data={},
        )
        result = CheckResult(
            record=record, status="error", error_message="Missing timeUnixNano field"
        )
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        output = format_result(result, start_ns, end_ns)

        assert "Line 8, Record 0: ERROR" in output
        assert "Missing timeUnixNano field" in output


class TestFormatSummary:
    """Test summary formatting."""

    def test_format_summary(self) -> None:
        """Test formatting summary with various counts."""
        summary = Summary(
            total_lines=10,
            total_records=42,
            in_range=38,
            too_early=1,
            too_late=1,
            errors=2,
        )

        output = format_summary(summary)

        assert "Total lines processed: 10" in output
        assert "Total log records: 42" in output
        assert "In range: 38" in output
        assert "Out of range (too early): 1" in output
        assert "Out of range (too late): 1" in output
        assert "Errors: 2" in output


class TestProcessStream:
    """Test stream processing logic."""

    def test_process_all_in_range(self) -> None:
        """Test processing where all timestamps are in range."""
        input_data = """{"resourceLogs":[{"scopeLogs":[{"logRecords":[{"timeUnixNano":"1592224245000000000"}]}]}]}
{"resourceLogs":[{"scopeLogs":[{"logRecords":[{"timeUnixNano":"1593224245000000000"}]}]}]}"""

        input_stream = io.StringIO(input_data)
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        summary, has_issues = process_stream(
            input_stream, start_ns, end_ns, verbose=False, quiet=True
        )

        assert summary.total_lines == 2
        assert summary.total_records == 2
        assert summary.in_range == 2
        assert summary.too_early == 0
        assert summary.too_late == 0
        assert summary.errors == 0
        assert has_issues is False

    def test_process_with_out_of_range(self) -> None:
        """Test processing with out-of-range timestamps."""
        input_data = """{"resourceLogs":[{"scopeLogs":[{"logRecords":[{"timeUnixNano":"1576408200000000000"}]}]}]}
{"resourceLogs":[{"scopeLogs":[{"logRecords":[{"timeUnixNano":"1615819530123000000"}]}]}]}"""

        input_stream = io.StringIO(input_data)
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        summary, has_issues = process_stream(
            input_stream, start_ns, end_ns, verbose=False, quiet=True
        )

        assert summary.total_lines == 2
        assert summary.total_records == 2
        assert summary.in_range == 0
        assert summary.too_early == 1
        assert summary.too_late == 1
        assert summary.errors == 0
        assert has_issues is True

    def test_process_with_missing_fields(self) -> None:
        """Test processing records with missing timeUnixNano."""
        input_data = '{"resourceLogs":[{"scopeLogs":[{"logRecords":[{"body":{"stringValue":"test"}}]}]}]}'

        input_stream = io.StringIO(input_data)
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        summary, has_issues = process_stream(
            input_stream, start_ns, end_ns, verbose=False, quiet=True
        )

        assert summary.total_lines == 1
        assert summary.total_records == 1
        assert summary.in_range == 0
        assert summary.errors == 1
        assert has_issues is True

    def test_process_invalid_json(self) -> None:
        """Test processing with invalid JSON."""
        input_data = "{invalid json"

        input_stream = io.StringIO(input_data)
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        summary, has_issues = process_stream(
            input_stream, start_ns, end_ns, verbose=False, quiet=True
        )

        assert summary.total_lines == 1
        assert summary.total_records == 0
        assert summary.errors == 1
        assert has_issues is True

    def test_process_multiple_records_per_line(self) -> None:
        """Test processing with multiple records in a single line."""
        input_data = '{"resourceLogs":[{"scopeLogs":[{"logRecords":[{"timeUnixNano":"1592224245000000000"},{"timeUnixNano":"1576408200000000000"},{"timeUnixNano":"1593224245000000000"}]}]}]}'

        input_stream = io.StringIO(input_data)
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        summary, has_issues = process_stream(
            input_stream, start_ns, end_ns, verbose=False, quiet=True
        )

        assert summary.total_lines == 1
        assert summary.total_records == 3
        assert summary.in_range == 2
        assert summary.too_early == 1
        assert has_issues is True

    def test_process_empty_input(self) -> None:
        """Test processing empty input stream."""
        input_stream = io.StringIO("")
        start_ns = 1577836800000000000
        end_ns = 1609459199999000000

        summary, has_issues = process_stream(
            input_stream, start_ns, end_ns, verbose=False, quiet=True
        )

        assert summary.total_lines == 0
        assert summary.total_records == 0
        assert has_issues is False
