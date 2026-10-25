export const fmtMW = (v, d = 0) =>
  v == null ? "–" : `${Number(v).toLocaleString("en-GB", { maximumFractionDigits: d })} MW`;
export const fmtNum = (v, d = 0) =>
  v == null ? "–" : Number(v).toLocaleString("en-GB", { maximumFractionDigits: d });
export const fmtMWh = (v) => (v == null ? "–" : `${Number(v).toLocaleString("en-GB", { maximumFractionDigits: 0 })} MWh`);
export const fmtPct = (v, d = 1) => (v == null ? "–" : `${Number(v).toFixed(d)}%`);
export const signed = (v, d = 0) =>
  v == null ? "–" : `${v > 0 ? "+" : ""}${Number(v).toLocaleString("en-GB", { maximumFractionDigits: d })}`;
export const fmtDay = (iso, opts = { weekday: "short", day: "numeric", month: "short" }) =>
  new Date(`${iso}T12:00:00Z`).toLocaleDateString("en-GB", { ...opts, timeZone: "UTC" });
export const fmtUtcStamp = (iso) =>
  iso ? new Date(iso).toLocaleString("en-GB", { timeZone: "Europe/London", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "–";
