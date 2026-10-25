"""Business logic: decision-time forecast selection and accuracy analytics.

"Decision forecast" for a target half-hour = the latest forecast whose publish
time is <= the day-ahead decision time on D-1, i.e. exactly what the trader
could see. Later vintages are never used (no look-ahead).
"""
from __future__ import annotations

import math
from datetime import date, datetime, time
from statistics import mean
from typing import Iterator

from ..data.models import Dataset, iso
from .metrics import error_metrics, rnd
from .timeutils import LONDON, decision_cutoff, delivery_dates, delivery_targets

HIST_BIN_MW = 500


class AnalysisService:
    """Stateless apart from a per-decision-time cache of the window accuracy."""

    def __init__(self, dataset: Dataset, decision_start: date, decision_end: date):
        self.ds = dataset
        self.days = delivery_dates(decision_start, decision_end)
        self._acc_cache: dict[time, dict] = {}

    # ---- selection -------------------------------------------------------
    def decision_pairs(self, delivery_date: date, decision_time: time
                       ) -> Iterator[tuple[datetime, datetime | None, float | None, float | None]]:
        """Yield (target, publish_time, forecast, actual) for each half-hour of a day."""
        cutoff = decision_cutoff(delivery_date, decision_time)
        for t in delivery_targets(delivery_date):
            series = self.ds.forecasts.get(t)
            fc = series.latest_at(cutoff) if series else None
            yield t, (fc[0] if fc else None), (fc[1] if fc else None), self.ds.actuals.get(t)

    def _window_rows(self, decision_time: time) -> list[tuple[date, datetime, float, float]]:
        return [(d, t, f, a) for d in self.days
                for t, _p, f, a in self.decision_pairs(d, decision_time) if f is not None and a is not None]

    # ---- day view --------------------------------------------------------
    def day_forecast(self, delivery_date: date, decision_time: time) -> dict:
        cutoff = decision_cutoff(delivery_date, decision_time)
        s = self.accuracy(decision_time)["summary"]
        q10, q90 = s.get("error_p10"), s.get("error_p90")

        periods = []
        for t, pub, f, a in self.decision_pairs(delivery_date, decision_time):
            row = {
                "start_time": iso(t),
                "local_time": t.astimezone(LONDON).strftime("%H:%M"),
                "settlement_period": len(periods) + 1,
                "forecast": rnd(f),
                "publish_time": iso(pub) if pub else None,
                "horizon_h": rnd((t - pub).total_seconds() / 3600) if pub else None,
                "actual": rnd(a),
                "error": rnd(f - a) if f is not None and a is not None else None,
                "lower": None, "upper": None,
            }
            if f is not None and q10 is not None and q90 is not None:
                # error = f - actual  =>  actual lies in [f - p90(err), f - p10(err)]
                row["lower"], row["upper"] = rnd(max(0.0, f - q90)), rnd(f - q10)
            periods.append(row)

        fvals = [p["forecast"] for p in periods if p["forecast"] is not None]
        avals = [p["actual"] for p in periods if p["actual"] is not None]
        lows = [p["lower"] for p in periods if p["lower"] is not None]
        pubs = [p["publish_time"] for p in periods if p["publish_time"]]
        pairs = [(p["forecast"], p["actual"]) for p in periods if p["forecast"] is not None and p["actual"] is not None]
        summary = {
            "forecast_energy_mwh": rnd(sum(fvals) * 0.5, 0) if fvals else None,
            "forecast_mean_mw": rnd(mean(fvals)) if fvals else None,
            "forecast_peak_mw": rnd(max(fvals)) if fvals else None,
            "forecast_min_mw": rnd(min(fvals)) if fvals else None,
            "low_case_energy_mwh": rnd(sum(lows) * 0.5, 0) if lows else None,
            "actual_energy_mwh": rnd(sum(avals) * 0.5, 0) if len(avals) == len(periods) else None,
            "latest_publish_time": max(pubs) if pubs else None,
            "earliest_publish_time": min(pubs) if pubs else None,
            "day_metrics": error_metrics(pairs),
            "complete": len(fvals) == len(periods),
        }
        return {
            "delivery_date": delivery_date.isoformat(),
            "decision_time_utc": iso(cutoff),
            "decision_time_local": cutoff.astimezone(LONDON).strftime("%Y-%m-%d %H:%M %Z"),
            "band_definition": "P10-P90 of historical (forecast - actual) error over the analysis window",
            "summary": summary,
            "periods": periods,
        }

    # ---- window accuracy -------------------------------------------------
    def accuracy(self, decision_time: time) -> dict:
        if decision_time not in self._acc_cache:
            self._acc_cache[decision_time] = self._compute_accuracy(decision_time)
        return self._acc_cache[decision_time]

    def _compute_accuracy(self, decision_time: time) -> dict:
        rows = self._window_rows(decision_time)
        pairs = [(f, a) for _, _, f, a in rows]

        by_day: dict[date, list] = {}
        by_hour: dict[int, list] = {h: [] for h in range(24)}
        for d, t, f, a in rows:
            by_day.setdefault(d, []).append((f, a))
            by_hour[t.astimezone(LONDON).hour].append((f, a))

        day_rows = []
        for d in sorted(by_day):
            m = error_metrics(by_day[d])
            day_rows.append({k: m[k] for k in ("n", "mae", "rmse", "bias", "mean_actual", "nmae_pct")} | {"date": d.isoformat()})
        hour_rows = [{"hour": h, "n": len(by_hour[h]), **{k: error_metrics(by_hour[h]).get(k) for k in ("mae", "bias")}}
                     for h in range(24)]

        histogram, errs = [], [f - a for f, a in pairs]
        if errs:
            lo = math.floor(min(errs) / HIST_BIN_MW) * HIST_BIN_MW
            hi = math.ceil((max(errs) + 1e-9) / HIST_BIN_MW) * HIST_BIN_MW
            counts: dict[int, int] = {}
            for e in errs:
                i = int((e - lo) // HIST_BIN_MW)
                counts[i] = counts.get(i, 0) + 1
            histogram = [{"bin_start": lo + i * HIST_BIN_MW, "bin_end": lo + (i + 1) * HIST_BIN_MW,
                          "count": counts.get(i, 0)} for i in range(int((hi - lo) // HIST_BIN_MW))]

        worst = sorted(rows, key=lambda r: abs(r[2] - r[3]), reverse=True)[:10]
        return {
            "decision_time": decision_time.strftime("%H:%M"),
            "delivery_window": [self.days[0].isoformat(), self.days[-1].isoformat()],
            "days_evaluated": len(by_day),
            "summary": error_metrics(pairs),
            "by_day": day_rows,
            "by_hour": hour_rows,
            "histogram": histogram,
            "worst_periods": [{"start_time": iso(t), "local": t.astimezone(LONDON).strftime("%d %b %H:%M"),
                               "forecast": rnd(f), "actual": rnd(a), "error": rnd(f - a)} for _, t, f, a in worst],
        }

    def horizon_accuracy(self, max_horizon_h: int = 48) -> list[dict]:
        """MAE/bias vs forecast horizon using every vintage (value of waiting for later forecasts)."""
        buckets: dict[int, list[float]] = {}
        for d in self.days:
            for t in delivery_targets(d):
                a, series = self.ds.actuals.get(t), self.ds.forecasts.get(t)
                if a is None or series is None:
                    continue
                for pub, f in zip(series.publish_times, series.values, strict=True):
                    h = (t - pub).total_seconds() / 3600
                    if 0 <= h < max_horizon_h:
                        buckets.setdefault(int(h), []).append(f - a)
        return [{"horizon_h": h, "n": len(e), "mae": rnd(mean(abs(x) for x in e)), "bias": rnd(mean(e))}
                for h, e in sorted(buckets.items())]
