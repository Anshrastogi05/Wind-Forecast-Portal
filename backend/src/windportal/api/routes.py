"""HTTP routes. Thin layer: validate input, delegate to ``AnalysisService``."""
from __future__ import annotations

from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import get_settings
from ..domain.service import AnalysisService
from . import schemas
from .deps import decision_time_param, get_dataset, get_service

router = APIRouter(prefix="/api")


@router.get("/health", response_model=schemas.Health, tags=["ops"])
def health():
    """Liveness probe."""
    return {"status": "ok"}


@router.get("/ready", response_model=schemas.Health, tags=["ops"])
def ready():
    """Readiness probe: dataset must be loadable and non-empty."""
    ds = get_dataset()
    if not ds.actuals or not ds.forecasts:
        raise HTTPException(503, "dataset empty - run ingestion")
    return {"status": "ready"}


@router.get("/meta", response_model=schemas.Meta, tags=["analytics"])
def meta(svc: AnalysisService = Depends(get_service)):
    s, ds = get_settings(), svc.ds
    return {
        "data_source": ds.source,
        "is_synthetic": ds.source.get("source") == "synthetic",
        "decision_window": [s.decision_start.isoformat(), s.decision_end.isoformat()],
        "delivery_dates": [d.isoformat() for d in svc.days],
        "default_decision_time": s.default_decision_time.strftime("%H:%M"),
        "timezone": "Europe/London",
        "n_actual_points": len(ds.actuals),
        "n_forecast_targets": len(ds.forecasts),
    }


@router.get("/forecast", response_model=schemas.DayForecast, tags=["analytics"])
def forecast(delivery_date: date, decision_time: time = Depends(decision_time_param),
             svc: AnalysisService = Depends(get_service)):
    """Latest forecast available at the day-ahead decision time for ``delivery_date``."""
    if delivery_date not in set(svc.days):
        raise HTTPException(404, "delivery_date outside the configured decision window")
    return svc.day_forecast(delivery_date, decision_time)


@router.get("/accuracy", response_model=schemas.Accuracy, tags=["analytics"])
def accuracy(decision_time: time = Depends(decision_time_param), svc: AnalysisService = Depends(get_service)):
    """Quantified accuracy of the decision-time forecast over the whole window."""
    result = svc.accuracy(decision_time)
    if result["summary"].get("n", 0) == 0:
        raise HTTPException(404, "No overlapping forecast/actual data. Run the ingestion first.")
    return result


@router.get("/horizon", response_model=schemas.Horizon, tags=["analytics"])
def horizon(max_horizon_h: int = Query(48, ge=1, le=168), svc: AnalysisService = Depends(get_service)):
    """Error vs forecast horizon across all published forecast vintages."""
    return {"max_horizon_h": max_horizon_h, "rows": svc.horizon_accuracy(max_horizon_h)}
