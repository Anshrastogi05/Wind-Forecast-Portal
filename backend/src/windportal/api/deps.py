"""Dependency providers (cached singletons, overridable in tests)."""
from __future__ import annotations

from datetime import time
from functools import lru_cache

from fastapi import HTTPException, Query

from ..config import Settings, get_settings
from ..data.models import Dataset
from ..data.repository import load_dataset
from ..domain.service import AnalysisService


@lru_cache(maxsize=1)
def get_dataset() -> Dataset:
    return load_dataset(get_settings().data_dir)


@lru_cache(maxsize=1)
def get_service() -> AnalysisService:
    s = get_settings()
    return AnalysisService(get_dataset(), s.decision_start, s.decision_end)


def decision_time_param(
    decision_time: str | None = Query(None, description="HH:MM Europe/London on D-1, half-hour granularity"),
) -> time:
    settings: Settings = get_settings()
    if decision_time is None:
        return settings.default_decision_time
    try:
        t = time.fromisoformat(decision_time)
    except ValueError:
        raise HTTPException(400, "decision_time must be HH:MM (Europe/London local time)") from None
    if t.minute % 30 != 0:
        raise HTTPException(400, "decision_time must be on a half-hour boundary")
    return t.replace(second=0, microsecond=0)
