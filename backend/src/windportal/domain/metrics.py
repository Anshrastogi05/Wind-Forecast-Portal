"""Pure statistics (stdlib only). error = forecast - actual (positive = over-forecast)."""
from __future__ import annotations

import math
from statistics import mean, median


def quantile(values: list[float], q: float) -> float | None:
    """Linear-interpolated quantile, q in [0, 1]."""
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    pos = q * (len(s) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def rnd(x: float | None, nd: int = 1) -> float | None:
    return None if x is None else round(x, nd)


def error_metrics(pairs: list[tuple[float, float]]) -> dict:
    """pairs = [(forecast, actual)] -> headline accuracy metrics."""
    if not pairs:
        return {"n": 0}
    errs = [f - a for f, a in pairs]
    abs_errs = [abs(e) for e in errs]
    mean_actual = mean(a for _, a in pairs)
    mae = mean(abs_errs)
    pct = [abs(f - a) / a for f, a in pairs if a > 0]
    return {
        "n": len(pairs),
        "mae": rnd(mae),
        "rmse": rnd(math.sqrt(mean(e * e for e in errs))),
        "bias": rnd(mean(errs)),
        "mape": rnd(100 * mean(pct), 2) if pct else None,
        "nmae_pct": rnd(100 * mae / mean_actual, 2) if mean_actual > 0 else None,
        "median_ae": rnd(median(abs_errs)),
        "p90_ae": rnd(quantile(abs_errs, 0.90)),
        "p95_ae": rnd(quantile(abs_errs, 0.95)),
        "max_ae": rnd(max(abs_errs)),
        "mean_actual": rnd(mean_actual),
        "over_forecast_pct": rnd(100 * sum(e > 0 for e in errs) / len(errs)),
        "under_forecast_pct": rnd(100 * sum(e < 0 for e in errs) / len(errs)),
        "error_p10": rnd(quantile(errs, 0.10)),
        "error_p50": rnd(quantile(errs, 0.50)),
        "error_p90": rnd(quantile(errs, 0.90)),
    }
