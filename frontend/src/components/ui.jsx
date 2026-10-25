import React from "react";

export function Kpi({ label, value, sub, tone }) {
  return (
    <div className={`kpi ${tone || ""}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

export function Card({ title, subtitle, children, className = "" }) {
  return (
    <section className={`card ${className}`}>
      {title && <h3>{title}</h3>}
      {subtitle && <p className="card-sub">{subtitle}</p>}
      {children}
    </section>
  );
}

export function Loading({ error }) {
  if (error) return <div className="state error">Could not load data – {error}</div>;
  return <div className="state">Loading…</div>;
}
