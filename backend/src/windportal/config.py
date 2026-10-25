"""Typed, environment-driven settings (12-factor). Read once via ``get_settings()``."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, time
from functools import lru_cache
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[2]


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    decision_start: date          # first day on which a decision is made
    decision_end: date            # last day on which a decision is made
    default_decision_time: time   # D-1 London local time
    max_horizon_hours: int
    elexon_base_url: str
    static_dir: Path | None       # built UI served by the API (single-container mode)
    cors_origins: list[str]
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        e = os.environ.get
        static = e("STATIC_DIR", "")
        return cls(
            data_dir=Path(e("DATA_DIR", _BACKEND_DIR / "data")),
            decision_start=date.fromisoformat(e("DECISION_START", "2026-01-01")),
            decision_end=date.fromisoformat(e("DECISION_END", "2026-01-31")),
            default_decision_time=time.fromisoformat(e("DEFAULT_DECISION_TIME", "09:00")),
            max_horizon_hours=int(e("MAX_HORIZON_HOURS", "48")),
            elexon_base_url=e("ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1"),
            static_dir=Path(static) if static else None,
            cors_origins=_csv(e("CORS_ORIGINS", "*")),
            log_level=e("LOG_LEVEL", "INFO").upper(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
