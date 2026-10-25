"""Loads the pre-ingested CSV files (UTC timestamps, MW) into a ``Dataset``.

  actuals.csv    start_time,generation
  forecasts.csv  publish_time,start_time,generation
  source.json    {"source": "elexon" | "synthetic", ...}
"""
from __future__ import annotations

import csv
import json
import logging
from datetime import timedelta
from pathlib import Path

from .models import Dataset, ForecastSeries, parse_ts

log = logging.getLogger(__name__)


def load_dataset(data_dir: Path) -> Dataset:
    actuals: dict = {}
    with (data_dir / "actuals.csv").open(newline="") as fh:
        for row in csv.DictReader(fh):
            actuals[parse_ts(row["start_time"])] = float(row["generation"])

    raw: dict = {}
    with (data_dir / "forecasts.csv").open(newline="") as fh:
        for row in csv.DictReader(fh):
            raw.setdefault(parse_ts(row["start_time"]), []).append(
                (parse_ts(row["publish_time"]), float(row["generation"]))
            )
    forecasts = {}
    for target, items in raw.items():
        items.sort(key=lambda x: x[0])
        forecasts[target] = ForecastSeries([p for p, _ in items], [v for _, v in items])

    # If forecasts are hourly (e.g. WINDFOR stream), propagate each hourly forecast
    # to the second half-hour settlement period (:30) of that hour.
    half_hour = timedelta(minutes=30)
    for target, series in list(forecasts.items()):
        half_target = target + half_hour
        if target.minute == 0 and half_target not in forecasts:
            forecasts[half_target] = series

    src = data_dir / "source.json"
    source = json.loads(src.read_text()) if src.exists() else {"source": "unknown"}
    log.info("Loaded %d actuals, %d forecast targets (source=%s)", len(actuals), len(forecasts), source.get("source"))
    return Dataset(actuals, forecasts, source)
