"""In-memory data model and timestamp helpers."""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
from datetime import datetime, timezone


def parse_ts(value: str) -> datetime:
    """Parse an ISO-8601 string into an aware UTC datetime."""
    dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ForecastSeries:
    """All forecast vintages for one target time, sorted by publish time."""

    publish_times: list[datetime] = field(default_factory=list)
    values: list[float] = field(default_factory=list)

    def latest_at(self, cutoff: datetime) -> tuple[datetime, float] | None:
        """Most recent forecast published at or before ``cutoff`` (None if none)."""
        i = bisect_right(self.publish_times, cutoff) - 1
        return None if i < 0 else (self.publish_times[i], self.values[i])


@dataclass
class Dataset:
    actuals: dict[datetime, float]
    forecasts: dict[datetime, ForecastSeries]
    source: dict
