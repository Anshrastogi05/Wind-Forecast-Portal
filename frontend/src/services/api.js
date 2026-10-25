// Thin API client. Relative URLs work with the Vite proxy, Docker and Vercel alike.
const BASE = import.meta.env.VITE_API_BASE || "";

async function get(path, params = {}) {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null)).toString();
  const res = await fetch(`${BASE}/api${path}${qs ? `?${qs}` : ""}`);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch { /* ignore */ }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

export const fetchMeta = () => get("/meta");
export const fetchForecast = (deliveryDate, decisionTime) =>
  get("/forecast", { delivery_date: deliveryDate, decision_time: decisionTime });
export const fetchAccuracy = (decisionTime) => get("/accuracy", { decision_time: decisionTime });
export const fetchHorizon = () => get("/horizon");
