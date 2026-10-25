import React, { useEffect, useState } from "react";
import { fetchMeta } from "../services/api";
import { Loading } from "../components/ui.jsx";
import DecisionPage from "../pages/DecisionPage.jsx";
import AccuracyPage from "../pages/AccuracyPage.jsx";

const DECISION_TIMES = ["06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00"];

export default function App() {
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("decision");
  const [decisionTime, setDecisionTime] = useState(null);

  useEffect(() => {
    fetchMeta()
      .then((m) => { setMeta(m); setDecisionTime(m.default_decision_time); })
      .catch((e) => setError(e.message));
  }, []);

  if (!meta) return <Loading error={error} />;

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Wind Forecast Portal</h1>
          <p>GB national wind generation · day-ahead procurement support</p>
        </div>
        <div className="decision-picker">
          <label htmlFor="dt">Day-ahead decision time (D-1, London)</label>
          <select id="dt" value={decisionTime} onChange={(e) => setDecisionTime(e.target.value)}>
            {DECISION_TIMES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </div>
      </header>

      {meta.is_synthetic && (
        <div className="banner">
          Demo mode: this deployment is showing <b>synthetic</b> data, not Elexon data. Run the ingestion
          (see README) to load the real FUELHH / WINDFOR data for January 2026.
        </div>
      )}

      <nav className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === "decision"} className={tab === "decision" ? "on" : ""} onClick={() => setTab("decision")}>
          1 · Forecast at decision time
        </button>
        <button role="tab" aria-selected={tab === "accuracy"} className={tab === "accuracy" ? "on" : ""} onClick={() => setTab("accuracy")}>
          2 · Forecast accuracy
        </button>
      </nav>

      <main>
        {tab === "decision" ? (
          <DecisionPage meta={meta} decisionTime={decisionTime} />
        ) : (
          <AccuracyPage decisionTime={decisionTime} />
        )}
      </main>

      <footer>
        Data: Elexon BMRS (FUELHH wind actuals, WINDFOR wind forecasts). Source in use:{" "}
        <b>{meta.data_source.source}</b>. Error = forecast − actual (positive = over-forecast).
      </footer>
    </div>
  );
}
