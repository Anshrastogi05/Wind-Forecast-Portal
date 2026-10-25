"""Pydantic response models: the typed public contract of the API (shown in /docs)."""
from __future__ import annotations

from pydantic import BaseModel


class Health(BaseModel):
    status: str


class Meta(BaseModel):
    data_source: dict
    is_synthetic: bool
    decision_window: list[str]
    delivery_dates: list[str]
    default_decision_time: str
    timezone: str
    n_actual_points: int
    n_forecast_targets: int


class Metrics(BaseModel):
    n: int
    mae: float | None = None
    rmse: float | None = None
    bias: float | None = None
    mape: float | None = None
    nmae_pct: float | None = None
    median_ae: float | None = None
    p90_ae: float | None = None
    p95_ae: float | None = None
    max_ae: float | None = None
    mean_actual: float | None = None
    over_forecast_pct: float | None = None
    under_forecast_pct: float | None = None
    error_p10: float | None = None
    error_p50: float | None = None
    error_p90: float | None = None


class Period(BaseModel):
    start_time: str
    local_time: str
    settlement_period: int
    forecast: float | None
    publish_time: str | None
    horizon_h: float | None
    actual: float | None
    error: float | None
    lower: float | None
    upper: float | None


class DaySummary(BaseModel):
    forecast_energy_mwh: float | None
    forecast_mean_mw: float | None
    forecast_peak_mw: float | None
    forecast_min_mw: float | None
    low_case_energy_mwh: float | None
    actual_energy_mwh: float | None
    latest_publish_time: str | None
    earliest_publish_time: str | None
    day_metrics: Metrics
    complete: bool


class DayForecast(BaseModel):
    delivery_date: str
    decision_time_utc: str
    decision_time_local: str
    band_definition: str
    summary: DaySummary
    periods: list[Period]


class DayError(BaseModel):
    date: str
    n: int
    mae: float | None
    rmse: float | None
    bias: float | None
    mean_actual: float | None
    nmae_pct: float | None


class HourError(BaseModel):
    hour: int
    n: int
    mae: float | None
    bias: float | None


class HistBin(BaseModel):
    bin_start: float
    bin_end: float
    count: int


class Miss(BaseModel):
    start_time: str
    local: str
    forecast: float | None
    actual: float | None
    error: float | None


class Accuracy(BaseModel):
    decision_time: str
    delivery_window: list[str]
    days_evaluated: int
    summary: Metrics
    by_day: list[DayError]
    by_hour: list[HourError]
    histogram: list[HistBin]
    worst_periods: list[Miss]


class HorizonRow(BaseModel):
    horizon_h: int
    n: int
    mae: float | None
    bias: float | None


class Horizon(BaseModel):
    max_horizon_h: int
    rows: list[HorizonRow]
