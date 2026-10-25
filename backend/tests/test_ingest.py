"""Ingestion tested against a mocked Elexon API (no network)."""
from datetime import date, datetime, timezone

import httpx

from windportal.ingest import elexon


def handler(request: httpx.Request) -> httpx.Response:
    if "FUELHH" in request.url.path:
        return httpx.Response(200, json=[
            {"fuelType": "WIND", "startTime": "2026-01-02T00:00:00Z", "generation": 5000},
            {"fuelType": "CCGT", "startTime": "2026-01-02T00:00:00Z", "generation": 9999},
        ])
    return httpx.Response(200, json=[
        {"publishTime": "2026-01-01T08:00:00Z", "startTime": "2026-01-02T00:00:00Z", "generation": 4800},
        {"publishTime": "2026-01-01T08:00:00Z", "startTime": "2026-01-09T00:00:00Z", "generation": 1},
    ])


def test_actuals_wind_only():
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        assert list(elexon.fetch_actuals(c, date(2026, 1, 2), date(2026, 1, 2)).values()) == [5000.0]


def test_forecasts_horizon_filter():
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        out = elexon.fetch_forecasts(c, datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 2, tzinfo=timezone.utc))
    assert list(out.values()) == [4800.0]
