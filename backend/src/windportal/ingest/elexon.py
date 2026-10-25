"""Ingest real wind actuals and forecasts from the Elexon BMRS Insights API.

    windportal ingest                 # uses window from settings
    windportal ingest --out data/    # custom output dir

Datasets (national level, no API key required):
  * FUELHH/stream  - actual half-hourly generation, filtered to fuelType == WIND
  * WINDFOR/stream - wind generation forecasts (publishTime, startTime, generation)

Only forecast vintages with horizon 0..MAX_HORIZON_HOURS ahead of their target
are kept to bound the data size.
"""
from __future__ import annotations

import csv
import json
import logging
import time as _time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

from ..config import Settings, get_settings
from ..data.models import iso, parse_ts
from ..domain.timeutils import delivery_dates

log = logging.getLogger(__name__)


def _get_json(client: httpx.Client, url: str, params: dict, retries: int = 4):
    for attempt in range(retries):
        try:
            r = client.get(url, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            return data["data"] if isinstance(data, dict) and "data" in data else data
        except (httpx.HTTPError, ValueError) as exc:
            if attempt == retries - 1:
                raise RuntimeError(f"Elexon request failed: {url} {params}: {exc}") from exc
            _time.sleep(2 ** attempt)


def fetch_actuals(client: httpx.Client, start: date, end: date, chunk_days: int = 7, base_url: str | None = None) -> dict[datetime, float]:
    base_url = base_url or get_settings().elexon_base_url
    out: dict[datetime, float] = {}
    d = start
    while d <= end:
        d_to = min(d + timedelta(days=chunk_days - 1), end)
        rows = _get_json(client, f"{base_url}/datasets/FUELHH/stream", {
            "settlementDateFrom": d.isoformat(),
            "settlementDateTo": d_to.isoformat(),
            "fuelType": "WIND",
        })
        for r in rows:
            if r.get("fuelType") == "WIND":
                out[parse_ts(r["startTime"])] = float(r["generation"])
        log.info(f"  actuals {d} -> {d_to}: {len(rows)} rows")
        d = d_to + timedelta(days=1)
    return out


def fetch_forecasts(client: httpx.Client, pub_from: datetime, pub_to: datetime, base_url: str | None = None, max_h: int | None = None) -> dict[tuple[datetime, datetime], float]:
    """Fetch WINDFOR by publish-time windows of 1 day (keeps responses small)."""
    out: dict[tuple[datetime, datetime], float] = {}
    t = pub_from
    base_url = base_url or get_settings().elexon_base_url
    max_h = max_h if max_h is not None else get_settings().max_horizon_hours
    while t < pub_to:
        t_to = min(t + timedelta(days=1), pub_to)
        rows = _get_json(client, f"{base_url}/datasets/WINDFOR/stream", {
            "publishDateTimeFrom": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publishDateTimeTo": t_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        kept = 0
        for r in rows:
            pub, tgt = parse_ts(r["publishTime"]), parse_ts(r["startTime"])
            if 0 <= (tgt - pub).total_seconds() / 3600 <= max_h and r.get("generation") is not None:
                out[(pub, tgt)] = float(r["generation"])
                kept += 1
        log.info(f"  forecasts published {t:%Y-%m-%d %H:%M} -> {t_to:%Y-%m-%d %H:%M}: {len(rows)} rows, kept {kept}")
        t = t_to
    return out


def run(out_dir: Path, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    days = delivery_dates(settings.decision_start, settings.decision_end)
    first, last = days[0], days[-1]
    log.info(f"Delivery days {first} .. {last}")
    out_dir.mkdir(parents=True, exist_ok=True)

    with httpx.Client(headers={"Accept": "application/json"}) as client:
        actuals = fetch_actuals(client, first - timedelta(days=1), last + timedelta(days=1))
        pub_from = datetime.combine(first - timedelta(days=3), datetime.min.time(), tzinfo=timezone.utc)
        pub_to = datetime.combine(last + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        forecasts = fetch_forecasts(client, pub_from, pub_to)

    with (out_dir / "actuals.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["start_time", "generation"])
        for k in sorted(actuals):
            w.writerow([iso(k), actuals[k]])
    with (out_dir / "forecasts.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["publish_time", "start_time", "generation"])
        for (pub, tgt) in sorted(forecasts):
            w.writerow([iso(pub), iso(tgt), forecasts[(pub, tgt)]])
    (out_dir / "source.json").write_text(json.dumps({
        "source": "elexon",
        "datasets": ["FUELHH (fuelType=WIND)", "WINDFOR"],
        "generated_at": iso(datetime.now(timezone.utc)),
        "actual_rows": len(actuals),
        "forecast_rows": len(forecasts),
    }, indent=2))
    log.info(f"Wrote {len(actuals)} actuals and {len(forecasts)} forecast rows to {out_dir}")
