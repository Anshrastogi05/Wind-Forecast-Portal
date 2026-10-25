def test_health_ready(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/ready").json() == {"status": "ready"}


def test_meta(client):
    r = client.get("/api/meta").json()
    assert r["delivery_dates"][0] == "2026-01-02" and r["delivery_dates"][-1] == "2026-02-01"


def test_forecast_no_lookahead_and_band(client):
    r = client.get("/api/forecast", params={"delivery_date": "2026-01-10"}).json()
    assert len(r["periods"]) == 48
    for p in r["periods"]:
        assert p["publish_time"] <= r["decision_time_utc"]
        assert p["lower"] <= p["forecast"] <= p["upper"]


def test_validation(client):
    assert client.get("/api/forecast", params={"delivery_date": "2026-03-01"}).status_code == 404
    assert client.get("/api/forecast", params={"delivery_date": "2026-01-10", "decision_time": "9am"}).status_code == 400
    assert client.get("/api/forecast", params={"delivery_date": "2026-01-10", "decision_time": "09:17"}).status_code == 400
    assert client.get("/api/forecast", params={"delivery_date": "nonsense"}).status_code == 422


def test_accuracy(client):
    r = client.get("/api/accuracy").json()
    assert r["summary"]["n"] > 1000 and len(r["by_hour"]) == 24 and r["days_evaluated"] == 31


def test_later_decision_not_worse(client):
    early = client.get("/api/accuracy", params={"decision_time": "06:00"}).json()["summary"]["mae"]
    late = client.get("/api/accuracy", params={"decision_time": "12:00"}).json()["summary"]["mae"]
    assert late <= early * 1.05


def test_horizon_trend(client):
    rows = client.get("/api/horizon").json()["rows"]
    assert rows[0]["mae"] < rows[-1]["mae"]


def test_openapi_published(client):
    assert client.get("/api/openapi.json").status_code == 200
