"""Tests for otlp_parser module."""

import json

import pytest

from otlp_analyzer.common.otlp_parser import OTLPParseError, parse_otlp_line


class TestParseOTLPLine:
    """Test OTLP JSONL parsing."""

    def test_parse_single_log_record(self) -> None:
        """Test parsing a line with a single log record."""
        line = json.dumps(
            {
                "resourceLogs": [
                    {
                        "scopeLogs": [
                            {
                                "logRecords": [
                                    {
                                        "timeUnixNano": "1577836800000000000",
                                        "body": {"stringValue": "test log"},
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )

        records = parse_otlp_line(line, 1)

        assert len(records) == 1
        assert records[0].time_unix_nano == 1577836800000000000
        assert records[0].line_number == 1
        assert records[0].record_index == 0

    def test_parse_multiple_log_records(self) -> None:
        """Test parsing a line with multiple log records."""
        line = json.dumps(
            {
                "resourceLogs": [
                    {
                        "scopeLogs": [
                            {
                                "logRecords": [
                                    {"timeUnixNano": "1577836800000000000"},
                                    {"timeUnixNano": "1577836801000000000"},
                                    {"timeUnixNano": "1577836802000000000"},
                                ]
                            }
                        ]
                    }
                ]
            }
        )

        records = parse_otlp_line(line, 1)

        assert len(records) == 3
        assert records[0].record_index == 0
        assert records[1].record_index == 1
        assert records[2].record_index == 2
        assert records[0].time_unix_nano == 1577836800000000000
        assert records[1].time_unix_nano == 1577836801000000000
        assert records[2].time_unix_nano == 1577836802000000000

    def test_parse_nested_arrays(self) -> None:
        """Test parsing with multiple resources and scopes."""
        line = json.dumps(
            {
                "resourceLogs": [
                    {
                        "scopeLogs": [
                            {"logRecords": [{"timeUnixNano": "1000000000000000000"}]},
                            {"logRecords": [{"timeUnixNano": "2000000000000000000"}]},
                        ]
                    },
                    {
                        "scopeLogs": [
                            {"logRecords": [{"timeUnixNano": "3000000000000000000"}]}
                        ]
                    },
                ]
            }
        )

        records = parse_otlp_line(line, 1)

        assert len(records) == 3
        assert records[0].time_unix_nano == 1000000000000000000
        assert records[1].time_unix_nano == 2000000000000000000
        assert records[2].time_unix_nano == 3000000000000000000

    def test_parse_integer_time_unix_nano(self) -> None:
        """Test parsing timeUnixNano as integer (not string)."""
        line = json.dumps(
            {
                "resourceLogs": [
                    {
                        "scopeLogs": [
                            {"logRecords": [{"timeUnixNano": 1577836800000000000}]}
                        ]
                    }
                ]
            }
        )

        records = parse_otlp_line(line, 1)

        assert len(records) == 1
        assert records[0].time_unix_nano == 1577836800000000000

    def test_parse_missing_time_unix_nano(self) -> None:
        """Test parsing log record without timeUnixNano field."""
        line = json.dumps(
            {
                "resourceLogs": [
                    {
                        "scopeLogs": [
                            {"logRecords": [{"body": {"stringValue": "test log"}}]}
                        ]
                    }
                ]
            }
        )

        records = parse_otlp_line(line, 1)

        assert len(records) == 1
        assert records[0].time_unix_nano is None

    def test_parse_invalid_time_unix_nano(self) -> None:
        """Test parsing log record with invalid timeUnixNano."""
        line = json.dumps(
            {
                "resourceLogs": [
                    {"scopeLogs": [{"logRecords": [{"timeUnixNano": "not-a-number"}]}]}
                ]
            }
        )

        records = parse_otlp_line(line, 1)

        assert len(records) == 1
        assert records[0].time_unix_nano is None

    def test_parse_empty_arrays(self) -> None:
        """Test parsing with empty arrays."""
        line = json.dumps({"resourceLogs": []})

        records = parse_otlp_line(line, 1)

        assert len(records) == 0

    def test_parse_empty_log_records(self) -> None:
        """Test parsing with empty logRecords array."""
        line = json.dumps({"resourceLogs": [{"scopeLogs": [{"logRecords": []}]}]})

        records = parse_otlp_line(line, 1)

        assert len(records) == 0

    def test_parse_empty_line(self) -> None:
        """Test parsing an empty line."""
        records = parse_otlp_line("", 1)
        assert len(records) == 0

    def test_parse_whitespace_line(self) -> None:
        """Test parsing a whitespace-only line."""
        records = parse_otlp_line("   \n  ", 1)
        assert len(records) == 0

    def test_parse_invalid_json(self) -> None:
        """Test that invalid JSON raises OTLPParseError."""
        line = "{invalid json"

        with pytest.raises(OTLPParseError):
            parse_otlp_line(line, 1)

    def test_parse_missing_resource_logs(self) -> None:
        """Test parsing JSON without resourceLogs field."""
        line = json.dumps({"other": "data"})

        records = parse_otlp_line(line, 1)

        assert len(records) == 0

    def test_parse_resource_logs_not_list(self) -> None:
        """Test parsing with resourceLogs that's not a list."""
        line = json.dumps({"resourceLogs": "not-a-list"})

        with pytest.raises(OTLPParseError):
            parse_otlp_line(line, 1)

    def test_line_number_tracking(self) -> None:
        """Test that line numbers are tracked correctly."""
        line = json.dumps(
            {
                "resourceLogs": [
                    {
                        "scopeLogs": [
                            {"logRecords": [{"timeUnixNano": "1000000000000000000"}]}
                        ]
                    }
                ]
            }
        )

        records = parse_otlp_line(line, 42)

        assert records[0].line_number == 42
