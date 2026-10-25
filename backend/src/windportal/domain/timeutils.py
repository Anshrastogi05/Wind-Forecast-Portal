"""Time helpers. Storage is UTC; delivery days / decision times are London local."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")
UTC = timezone.utc
STEP = timedelta(minutes=30)


def local_midnight_utc(d: date) -> datetime:
    return datetime.combine(d, time(0, 0), tzinfo=LONDON).astimezone(UTC)


def delivery_targets(delivery_date: date) -> list[datetime]:
    """Half-hour start times (UTC) of a London-local delivery day (46/48/50 on DST days)."""
    start, end = local_midnight_utc(delivery_date), local_midnight_utc(delivery_date + timedelta(days=1))
    out, t = [], start
    while t < end:
        out.append(t)
        t += STEP
    return out


def decision_cutoff(delivery_date: date, decision_time: time) -> datetime:
    """UTC instant of the day-ahead decision: D-1 at ``decision_time`` London time."""
    return datetime.combine(delivery_date - timedelta(days=1), decision_time, tzinfo=LONDON).astimezone(UTC)


def delivery_dates(decision_start: date, decision_end: date) -> list[date]:
    """Delivery days = decision day + 1, for every decision day in the window."""
    out, d = [], decision_start
    while d <= decision_end:
        out.append(d + timedelta(days=1))
        d += timedelta(days=1)
    return out
