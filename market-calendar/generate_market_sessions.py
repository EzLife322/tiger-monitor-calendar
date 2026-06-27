#!/usr/bin/env python3
"""
Generate TigerMonitor market-sessions.csv from exchange_calendars.

Output format:
  REGION|OPEN_UNIX_UTC|CLOSE_UNIX_UTC

Regions currently used by TigerMonitor:
  AS = Asia aggregate
  EU = Europe aggregate
  US = United States aggregate

The generator writes separate intervals around exchange lunch breaks when the
calendar exposes break_start / break_end values.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import exchange_calendars as xcals
import pandas as pd


DEFAULT_EXCHANGES = {
    "AS": ("XTKS", "XHKG"),
    "EU": ("XLON", "XETR"),
    "US": ("XNYS",),
}


def utc_timestamp(value) -> int:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return int(ts.timestamp())


def as_utc_timestamp(value) -> Optional[pd.Timestamp]:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def get_schedule(calendar, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Return schedule with a few compatibility paths for exchange_calendars."""
    try:
        schedule = calendar.schedule.loc[start:end]
        if isinstance(schedule, pd.DataFrame):
            return schedule
    except Exception:
        pass

    try:
        return calendar.schedule(start, end)
    except Exception:
        pass

    sessions = calendar.sessions_in_range(start, end)
    rows = []
    for session in sessions:
        row = {
            "market_open": calendar.session_open(session),
            "market_close": calendar.session_close(session),
        }
        for name, method_name in (
            ("break_start", "session_break_start"),
            ("break_end", "session_break_end"),
        ):
            try:
                row[name] = getattr(calendar, method_name)(session)
            except Exception:
                row[name] = pd.NaT
        rows.append(row)
    return pd.DataFrame(rows, index=sessions)


def column_value(row: pd.Series, *names: str):
    lowered = {str(key).lower(): key for key in row.index}
    for name in names:
        key = lowered.get(name.lower())
        if key is not None:
            return row[key]
    return None


def iter_calendar_intervals(exchange: str, start: pd.Timestamp, end: pd.Timestamp):
    calendar = xcals.get_calendar(exchange)
    schedule = get_schedule(calendar, start, end)
    for _, row in schedule.iterrows():
        open_ts = as_utc_timestamp(column_value(row, "market_open", "open"))
        close_ts = as_utc_timestamp(column_value(row, "market_close", "close"))
        if open_ts is None or close_ts is None or close_ts <= open_ts:
            continue

        break_start = as_utc_timestamp(column_value(row, "break_start", "market_break_start"))
        break_end = as_utc_timestamp(column_value(row, "break_end", "market_break_end"))
        if break_start is not None and break_end is not None and open_ts < break_start < break_end < close_ts:
            yield open_ts, break_start
            yield break_end, close_ts
        else:
            yield open_ts, close_ts


def merge_intervals(intervals: Iterable[Tuple[pd.Timestamp, pd.Timestamp]]):
    ordered = sorted(intervals, key=lambda item: (item[0], item[1]))
    merged: List[Tuple[pd.Timestamp, pd.Timestamp]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        elif end > merged[-1][1]:
            merged[-1] = (merged[-1][0], end)
    return merged


def generate(start: dt.date, end: dt.date) -> str:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    lines = [
        "# Generated from exchange_calendars",
        f"# Range: {start.isoformat()}..{end.isoformat()}",
        "# Format: REGION|OPEN_UNIX_UTC|CLOSE_UNIX_UTC",
    ]
    for region, exchanges in DEFAULT_EXCHANGES.items():
        intervals = []
        for exchange in exchanges:
            intervals.extend(iter_calendar_intervals(exchange, start_ts, end_ts))
        for open_ts, close_ts in merge_intervals(intervals):
            lines.append(f"{region}|{utc_timestamp(open_ts)}|{utc_timestamp(close_ts)}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    today = dt.date.today()
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="market-sessions.csv")
    parser.add_argument("--start", default=(today - dt.timedelta(days=30)).isoformat())
    parser.add_argument("--days", type=int, default=730)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = dt.date.fromisoformat(args.start)
    end = start + dt.timedelta(days=max(1, args.days))
    output = Path(args.output)
    output.write_text(generate(start, end), encoding="utf-8", newline="\n")
    print(f"wrote {output} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
