"""CLI tool to check if OTLP log record timestamps fall within a time range."""

import sys
from dataclasses import dataclass
from typing import TextIO

import click

from otlp_analyzer.common.otlp_parser import LogRecord, OTLPParseError, parse_otlp_line
from otlp_analyzer.common.timestamp_parser import TimestampParseError, parse_timestamp
from otlp_analyzer.common.utils import format_difference, format_timestamp


@dataclass
class CheckResult:
    """Result of checking a single log record."""

    record: LogRecord
    status: str  # "in_range", "too_early", "too_late", "error"
    error_message: str = ""


@dataclass
class Summary:
    """Summary of all checks performed."""

    total_lines: int = 0
    total_records: int = 0
    in_range: int = 0
    too_early: int = 0
    too_late: int = 0
    errors: int = 0


def check_timestamp_range(record: LogRecord, start_ns: int, end_ns: int) -> CheckResult:
    """
    Check if a log record's timestamp falls within the specified range.

    Args:
        record: The log record to check
        start_ns: Start of time range in nanoseconds
        end_ns: End of time range in nanoseconds

    Returns:
        CheckResult indicating the status
    """
    if record.time_unix_nano is None:
        return CheckResult(
            record=record,
            status="error",
            error_message="Missing or invalid timeUnixNano field",
        )

    if record.time_unix_nano < start_ns:
        return CheckResult(record=record, status="too_early")
    if record.time_unix_nano > end_ns:
        return CheckResult(record=record, status="too_late")
    return CheckResult(record=record, status="in_range")


def format_result(result: CheckResult, start_ns: int, end_ns: int) -> str:
    """
    Format a check result as a human-readable string.

    Args:
        result: The check result to format
        start_ns: Start of time range in nanoseconds
        end_ns: End of time range in nanoseconds

    Returns:
        Formatted string for output
    """
    lines = []
    record = result.record

    # Header line
    if result.status == "in_range":
        header = f"Line {record.line_number}, Record {record.record_index}: IN RANGE"
        lines.append(header)
    elif result.status == "too_early":
        header = (
            f"Line {record.line_number}, Record {record.record_index}: "
            f"OUT OF RANGE (too early)"
        )
        lines.append(header)
        if record.time_unix_nano is not None:
            lines.append(
                f"  timeUnixNano:    {format_timestamp(record.time_unix_nano)} "
                f"({record.time_unix_nano})"
            )
            lines.append(
                f"  expected range:  {format_timestamp(start_ns)} - "
                f"{format_timestamp(end_ns)}"
            )
            difference = start_ns - record.time_unix_nano
            lines.append(
                f"  difference:      {format_difference(difference, 'before start')}"
            )
    elif result.status == "too_late":
        header = (
            f"Line {record.line_number}, Record {record.record_index}: "
            f"OUT OF RANGE (too late)"
        )
        lines.append(header)
        if record.time_unix_nano is not None:
            lines.append(
                f"  timeUnixNano:    {format_timestamp(record.time_unix_nano)} "
                f"({record.time_unix_nano})"
            )
            lines.append(
                f"  expected range:  {format_timestamp(start_ns)} - "
                f"{format_timestamp(end_ns)}"
            )
            difference = record.time_unix_nano - end_ns
            lines.append(
                f"  difference:      {format_difference(difference, 'after end')}"
            )
    elif result.status == "error":
        header = (
            f"Line {record.line_number}, Record {record.record_index}: "
            f"ERROR - {result.error_message}"
        )
        lines.append(header)

    return "\n".join(lines)


def format_summary(summary: Summary) -> str:
    """
    Format the summary of all checks.

    Args:
        summary: Summary data structure

    Returns:
        Formatted summary string
    """
    lines = [
        "---",
        "Summary:",
        f"  Total lines processed: {summary.total_lines}",
        f"  Total log records: {summary.total_records}",
        f"  In range: {summary.in_range}",
        f"  Out of range (too early): {summary.too_early}",
        f"  Out of range (too late): {summary.too_late}",
        f"  Errors: {summary.errors}",
    ]
    return "\n".join(lines)


def process_stream(
    input_stream: TextIO,
    start_ns: int,
    end_ns: int,
    verbose: bool,
    quiet: bool,
) -> tuple[Summary, bool]:
    """
    Process JSONL input stream and check timestamps.

    Args:
        input_stream: Input stream to read JSONL from
        start_ns: Start of time range in nanoseconds
        end_ns: End of time range in nanoseconds
        verbose: Show all records (including in-range)
        quiet: Only show summary

    Returns:
        Tuple of (Summary, has_issues) where has_issues is True if any
        records were out of range or had errors
    """
    summary = Summary()
    has_issues = False

    for line_number, line in enumerate(input_stream, start=1):
        summary.total_lines += 1

        # Parse the line
        try:
            records = parse_otlp_line(line, line_number)
        except OTLPParseError as e:
            if not quiet:
                click.echo(f"Line {line_number}: ERROR - {e}")
            summary.errors += 1
            has_issues = True
            continue

        # Check each record
        for record in records:
            summary.total_records += 1
            result = check_timestamp_range(record, start_ns, end_ns)

            # Update summary
            if result.status == "in_range":
                summary.in_range += 1
            elif result.status == "too_early":
                summary.too_early += 1
                has_issues = True
            elif result.status == "too_late":
                summary.too_late += 1
                has_issues = True
            elif result.status == "error":
                summary.errors += 1
                has_issues = True

            # Output based on verbosity
            if not quiet:
                if verbose or result.status != "in_range":
                    click.echo(format_result(result, start_ns, end_ns))
                    click.echo()  # Blank line between records

    return summary, has_issues


@click.command()
@click.option(
    "--start",
    required=True,
    help="Start of time range (ISO 8601, Unix timestamp, or date string)",
)
@click.option(
    "--end",
    required=True,
    help="End of time range (ISO 8601, Unix timestamp, or date string)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show all log records (in range and out of range)",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Only show summary counts",
)
def main(start: str, end: str, verbose: bool, quiet: bool) -> None:
    """
    Check if OTLP log record timestamps fall within a time range.

    Reads JSONL from stdin and validates that timeUnixNano fields are within
    the specified start and end times (inclusive).

    Examples:

        cat logs.jsonl | otlp-check-timestamp --start 2020-01-01 --end 2020-12-31

        otlp-check-timestamp --start 1577836800 --end 1609459199 < logs.jsonl
    """
    # Parse time range arguments
    try:
        start_ns = parse_timestamp(start)
        end_ns = parse_timestamp(end)
    except TimestampParseError as e:
        click.echo(f"Error parsing time range: {e}", err=True)
        sys.exit(2)

    # Validate time range
    if start_ns >= end_ns:
        click.echo("Error: start time must be before end time", err=True)
        sys.exit(2)

    # Process input stream
    summary, has_issues = process_stream(sys.stdin, start_ns, end_ns, verbose, quiet)

    # Output summary
    if quiet:
        click.echo(
            f"In range: {summary.in_range}, Out of range: "
            f"{summary.too_early + summary.too_late}, Errors: {summary.errors}"
        )
    else:
        click.echo(format_summary(summary))

    # Exit with appropriate code
    sys.exit(1 if has_issues else 0)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
