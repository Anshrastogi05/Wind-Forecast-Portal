import React, { useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, ComposedChart, Legend, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { fetchAccuracy, fetchHorizon } from "../services/api";
import { Card, Kpi, Loading } from "../components/ui.jsx";
import { fmtDay, fmtMW, fmtNum, fmtPct, signed } from "../utils/format";

const grid = <CartesianGrid strokeDasharray="3 3" stroke="#e5e9f0" />;

export default function AccuracyPage({ decisionTime }) {
  const [acc, setAcc] = useState(null);
  const [hor, setHor] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setAcc(null); setError(null);
    fetchAccuracy(decisionTime).then(setAcc).catch((e) => setError(e.message));
  }, [decisionTime]);
  useEffect(() => { fetchHorizon().then((r) => setHor(r.rows)).catch(() => setHor([])); }, []);

  if (!acc) return <Loading error={error} />;
  const s = acc.summary;
  const dir = s.bias > 0 ? "over-forecasts" : "under-forecasts";
  const worstDay = [...acc.by_day].sort((a, b) => b.mae - a.mae)[0];
  const bestDay = [...acc.by_day].sort((a, b) => a.mae - b.mae)[0];

  return (
    <>
      <div className="callout">
        <b>How good is the forecast you actually trade on?</b> Over {acc.days_evaluated} delivery days
        ({fmtDay(acc.delivery_window[0])} – {fmtDay(acc.delivery_window[1])}) and {fmtNum(s.n)} half-hours, the forecast available
        at {acc.decision_time} on D-1 missed actual wind by <b>{fmtMW(s.mae)}</b> on average ({fmtPct(s.nmae_pct)} of mean output).
        It typically {dir} by {fmtMW(Math.abs(s.bias))}, and 1 half-hour in 10 is off by more than <b>{fmtMW(s.p90_ae)}</b>.
        Errors were smallest on {fmtDay(bestDay.date)} ({fmtMW(bestDay.mae)}) and largest on {fmtDay(worstDay.date)} ({fmtMW(worstDay.mae)}).
      </div>

      <div className="kpis">
        <Kpi label="MAE" value={fmtMW(s.mae)} sub="mean absolute error" />
        <Kpi label="RMSE" value={fmtMW(s.rmse)} sub="penalises large misses" />
        <Kpi label="Bias (mean error)" value={`${signed(s.bias)} MW`} sub={s.bias > 0 ? "over-forecast on average" : "under-forecast on average"} tone={Math.abs(s.bias) > 0.1 * s.mae ? "warn" : ""} />
        <Kpi label="nMAE" value={fmtPct(s.nmae_pct)} sub="MAE ÷ mean actual output" />
        <Kpi label="MAPE" value={fmtPct(s.mape)} sub="excludes zero-output periods" />
        <Kpi label="P90 / P95 abs. error" value={`${fmtNum(s.p90_ae)} / ${fmtNum(s.p95_ae)} MW`} sub="tail risk" tone="warn" />
        <Kpi label="P10 – P90 of error" value={`${fmtNum(s.error_p10)} … ${signed(s.error_p90)} MW`} sub="80% of errors fall in this range" />
        <Kpi label="Over / under share" value={`${fmtPct(s.over_forecast_pct, 0)} / ${fmtPct(s.under_forecast_pct, 0)}`} sub="of half-hours" />
      </div>

      <div className="grid2">
        <Card title="Daily error" subtitle="MAE (bars) and bias (line) per delivery day, MW.">
          <div className="chart">
            <ResponsiveContainer>
              <ComposedChart data={acc.by_day} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                {grid}
                <XAxis dataKey="date" tickFormatter={(d) => d.slice(8)} tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} width={48} />
                <Tooltip labelFormatter={(d) => fmtDay(d)} formatter={(v, n) => [`${fmtNum(v)} MW`, n]} />
                <Legend />
                <ReferenceLine y={0} stroke="#888" />
                <Bar dataKey="mae" name="MAE" fill="#2f6fed" isAnimationActive={false} />
                <Line dataKey="bias" name="Bias" stroke="#e8590c" strokeWidth={2} dot={false} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Error by time of day" subtitle="Which half-hours are hardest to forecast (London hour).">
          <div className="chart">
            <ResponsiveContainer>
              <ComposedChart data={acc.by_hour} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                {grid}
                <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} width={48} />
                <Tooltip formatter={(v, n) => [`${fmtNum(v)} MW`, n]} labelFormatter={(h) => `${String(h).padStart(2, "0")}:00`} />
                <Legend />
                <ReferenceLine y={0} stroke="#888" />
                <Bar dataKey="mae" name="MAE" fill="#2f6fed" isAnimationActive={false} />
                <Line dataKey="bias" name="Bias" stroke="#e8590c" strokeWidth={2} dot={false} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Error distribution" subtitle="Histogram of forecast − actual (500 MW bins). Right of zero = over-forecast.">
          <div className="chart">
            <ResponsiveContainer>
              <BarChart data={acc.histogram} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                {grid}
                <XAxis dataKey="bin_start" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v / 1000}k`} />
                <YAxis tick={{ fontSize: 11 }} width={40} />
                <Tooltip labelFormatter={(v) => `${fmtNum(v)} to ${fmtNum(v + 500)} MW`} formatter={(v) => [v, "half-hours"]} />
                <ReferenceLine x={0} stroke="#888" />
                <Bar dataKey="count" fill="#7048e8" isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Error vs forecast horizon" subtitle="MAE of every forecast vintage by hours-before-delivery: the cost of deciding earlier.">
          <div className="chart">
            {hor == null ? <Loading /> : (
              <ResponsiveContainer>
                <ComposedChart data={hor} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  {grid}
                  <XAxis dataKey="horizon_h" tick={{ fontSize: 11 }} label={{ value: "hours ahead", position: "insideBottom", offset: -2, fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} width={48} />
                  <Tooltip formatter={(v, n) => [`${fmtNum(v)} MW`, n]} labelFormatter={(h) => `${h}–${h + 1} h ahead`} />
                  <Legend />
                  <Line dataKey="mae" name="MAE" stroke="#2f6fed" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line dataKey="bias" name="Bias" stroke="#e8590c" strokeWidth={2} dot={false} isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>
      </div>

      <Card title="Ten largest misses" subtitle="Half-hours where the decision-time forecast was furthest from actual.">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Half-hour (London)</th><th>Forecast (MW)</th><th>Actual (MW)</th><th>Error (MW)</th></tr></thead>
            <tbody>
              {acc.worst_periods.map((w) => (
                <tr key={w.start_time}><td>{w.local}</td><td>{fmtNum(w.forecast)}</td><td>{fmtNum(w.actual)}</td>
                  <td className={w.error > 0 ? "pos" : "neg"}>{signed(w.error)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Method notes">
        <ul className="notes">
          <li><b>Decision-time forecast:</b> for each target half-hour, the latest WINDFOR value with <code>publishTime</code> ≤ {acc.decision_time} (London) on the previous day. Later forecasts are ignored, as the trader could not see them.</li>
          <li><b>Actuals:</b> FUELHH <code>generation</code> for <code>fuelType = WIND</code>.</li>
          <li><b>Error</b> = forecast − actual. nMAE normalises by mean actual output. MAPE excludes periods with zero actual output.</li>
          <li><b>P10–P90 band</b> on the forecast page is the empirical error range of this same window (in-sample), a pragmatic guide rather than a calibrated probabilistic forecast.</li>
        </ul>
      </Card>
    </>
  );
}
