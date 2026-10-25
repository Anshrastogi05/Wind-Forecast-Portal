import React, { useEffect, useMemo, useState } from "react";
import {
  Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { fetchForecast } from "../services/api";
import { Card, Kpi, Loading } from "../components/ui.jsx";
import { fmtDay, fmtMW, fmtMWh, fmtNum, fmtUtcStamp, signed } from "../utils/format";

export default function DecisionPage({ meta, decisionTime }) {
  const dates = meta.delivery_dates;
  const [date, setDate] = useState(dates[0]);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null); setError(null);
    fetchForecast(date, decisionTime).then(setData).catch((e) => setError(e.message));
  }, [date, decisionTime]);

  const chart = useMemo(
    () => (data ? data.periods.map((p) => ({
      ...p,
      band: p.lower != null ? [p.lower, p.upper] : null,
    })) : []),
    [data],
  );

  const idx = dates.indexOf(date);
  if (!data) return (
    <>
      <DayPicker dates={dates} date={date} setDate={setDate} idx={idx} />
      <Loading error={error} />
    </>
  );
  const s = data.summary;
  const hasActuals = s.actual_energy_mwh != null;

  return (
    <>
      <DayPicker dates={dates} date={date} setDate={setDate} idx={idx} />

      <div className="callout">
        <b>What you knew when you had to decide.</b> For delivery on <b>{fmtDay(date, { weekday: "long", day: "numeric", month: "long" })}</b>,
        the bid is placed on <b>{data.decision_time_local}</b>. The curve below uses, for every half-hour, the most recent
        WINDFOR forecast published up to that moment (latest vintage: <b>{fmtUtcStamp(s.latest_publish_time)}</b>).
      </div>

      <div className="kpis">
        <Kpi label="Expected wind energy" value={fmtMWh(s.forecast_energy_mwh)} sub={`avg ${fmtMW(s.forecast_mean_mw)}`} />
        <Kpi label="Peak / minimum" value={`${fmtNum(s.forecast_peak_mw)} / ${fmtNum(s.forecast_min_mw)} MW`} sub="forecast range across the day" />
        <Kpi label="Low-case wind energy" value={fmtMWh(s.low_case_energy_mwh)}
             sub="if errors land at the historical P90 over-forecast" tone="warn" />
        <Kpi label="Hedge to consider" value={s.low_case_energy_mwh != null ? fmtMWh(s.forecast_energy_mwh - s.low_case_energy_mwh) : "–"}
             sub="extra non-wind energy to cover the low case" tone="warn" />
        {hasActuals && <Kpi label="Actual wind energy" value={fmtMWh(s.actual_energy_mwh)}
             sub={`${signed(s.forecast_energy_mwh - s.actual_energy_mwh)} MWh forecast error`} tone="ok" />}
      </div>

      <Card title="Wind generation: decision-time forecast vs actual"
            subtitle="Shaded area = P10–P90 range of the forecast, derived from the historical error of this forecast (see Accuracy tab).">
        <div className="chart tall">
          <ResponsiveContainer>
            <ComposedChart data={chart} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e9f0" />
              <XAxis dataKey="local_time" interval={5} tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${v / 1000}GW`} width={52} />
              <Tooltip content={<DayTooltip />} />
              <Legend />
              <Area dataKey="band" name="P10–P90 range" stroke="none" fill="#2f6fed" fillOpacity={0.14} isAnimationActive={false} />
              <Line dataKey="forecast" name="Forecast at decision time" stroke="#2f6fed" strokeWidth={2.5} dot={false} isAnimationActive={false} />
              {hasActuals && <Line dataKey="actual" name="Actual" stroke="#e8590c" strokeWidth={2} dot={false} isAnimationActive={false} />}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card title="Half-hourly detail" subtitle="Times are Europe/London. Horizon = hours between forecast publication and delivery.">
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Period</th><th>Time</th><th>Forecast (MW)</th><th>P10</th><th>P90</th><th>Published</th><th>Horizon (h)</th>
                {hasActuals && <><th>Actual (MW)</th><th>Error (MW)</th></>}</tr>
            </thead>
            <tbody>
              {data.periods.map((p) => (
                <tr key={p.start_time}>
                  <td>{p.settlement_period}</td><td>{p.local_time}</td>
                  <td>{fmtNum(p.forecast)}</td><td>{fmtNum(p.lower)}</td><td>{fmtNum(p.upper)}</td>
                  <td>{fmtUtcStamp(p.publish_time)}</td><td>{fmtNum(p.horizon_h, 1)}</td>
                  {hasActuals && <><td>{fmtNum(p.actual)}</td><td className={p.error > 0 ? "pos" : "neg"}>{signed(p.error)}</td></>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}

function DayPicker({ dates, date, setDate, idx }) {
  return (
    <div className="daypicker">
      <button disabled={idx <= 0} onClick={() => setDate(dates[idx - 1])} aria-label="Previous day">‹</button>
      <label>
        Delivery day
        <select value={date} onChange={(e) => setDate(e.target.value)}>
          {dates.map((d) => <option key={d} value={d}>{fmtDay(d, { weekday: "short", day: "numeric", month: "short", year: "numeric" })}</option>)}
        </select>
      </label>
      <button disabled={idx >= dates.length - 1} onClick={() => setDate(dates[idx + 1])} aria-label="Next day">›</button>
    </div>
  );
}

function DayTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="tooltip">
      <b>{label}</b>
      <div>Forecast: {fmtMW(p.forecast)}</div>
      {p.lower != null && <div>P10–P90: {fmtNum(p.lower)} – {fmtNum(p.upper)} MW</div>}
      {p.actual != null && <div>Actual: {fmtMW(p.actual)} ({signed(p.error)} MW)</div>}
      <div className="muted">Published {fmtUtcStamp(p.publish_time)}</div>
    </div>
  );
}
