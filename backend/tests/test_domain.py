from datetime import date, datetime, time, timezone

import pytest

from windportal.data.models import Dataset, ForecastSeries
from windportal.domain import metrics, timeutils
from windportal.domain.service import AnalysisService

UTC = timezone.utc
T = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)


@pytest.fixture
def svc():
    fs = ForecastSeries(
        publish_times=[datetime(2026, 1, 1, h, 0, tzinfo=UTC) for h in (6, 9, 12)],
        values=[1000.0, 2000.0, 3000.0],
    )
    ds = Dataset(actuals={T: 2500.0}, forecasts={T: fs}, source={"source": "test"})
    return AnalysisService(ds, date(2026, 1, 1), date(2026, 1, 31))


def first(svc, hhmm):
    return next(iter(svc.decision_pairs(date(2026, 1, 2), time.fromisoformat(hhmm))))


def test_cutoff_inclusive_latest_vintage(svc):
    t, pub, f, a = first(svc, "09:00")
    assert (t, f, a) == (T, 2000.0, 2500.0)      # 09:00 vintage included, 12:00 excluded


def test_earlier_cutoff_earlier_vintage(svc):
    assert first(svc, "08:00")[2] == 1000.0


def test_no_vintage_before_cutoff(svc):
    assert first(svc, "05:00")[2] is None


def test_delivery_window_is_decision_plus_one():
    days = timeutils.delivery_dates(date(2026, 1, 1), date(2026, 1, 31))
    assert days[0] == date(2026, 1, 2) and days[-1] == date(2026, 2, 1) and len(days) == 31


@pytest.mark.parametrize("d,n", [(date(2026, 1, 15), 48), (date(2026, 3, 29), 46), (date(2026, 10, 25), 50)])
def test_period_counts_incl_dst(d, n):
    assert len(timeutils.delivery_targets(d)) == n


def test_error_metrics_values():
    m = metrics.error_metrics([(110.0, 100.0), (90.0, 100.0), (130.0, 100.0)])
    assert m["mae"] == pytest.approx(16.7, abs=0.05)
    assert m["bias"] == pytest.approx(10.0)
    assert m["rmse"] == pytest.approx((1100 / 3) ** 0.5, abs=0.05)
    assert m["nmae_pct"] == pytest.approx(16.67, abs=0.01)


def test_empty_and_zero_actual_handling():
    assert metrics.error_metrics([]) == {"n": 0}
    assert metrics.error_metrics([(10.0, 0.0), (110.0, 100.0)])["mape"] == pytest.approx(10.0)


def test_quantile():
    assert metrics.quantile([1, 2, 3, 4], 0.5) == 2.5
    assert metrics.quantile([], 0.5) is None
