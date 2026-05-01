"""
Benchmark clock anchor.

All seed/reset/verify scripts and any time-relative grading logic must read
the anchor from here so a date change touches one file, not seven.

Override at runtime via env vars:
    BENCHMARK_NOW  ISO 8601 with offset, e.g. 2026-04-19T10:00:00-07:00
    BENCH_TZ       Hour offset as a number, e.g. -7
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone


def _parse_tz(value: str | None, default: timezone) -> timezone:
    if not value:
        return default
    return timezone(timedelta(hours=float(value)))


def _parse_now(value: str | None, default: datetime) -> datetime:
    if not value:
        return default
    return datetime.fromisoformat(value)


BENCH_TZ: timezone = _parse_tz(os.environ.get("BENCH_TZ"), timezone(timedelta(hours=-7)))
BENCHMARK_NOW: datetime = _parse_now(
    os.environ.get("BENCHMARK_NOW"),
    datetime(2026, 4, 19, 10, 0, 0, tzinfo=BENCH_TZ),
)
BENCHMARK_NOW_EPOCH: float = BENCHMARK_NOW.timestamp()
