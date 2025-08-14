import React, { useEffect, useState } from "react";
import Card from "../../components/Card.jsx";
import { api } from "../../lib/api.js";

// --- date helpers (local timezone) ---
function addDays(d, days) {
  const x = new Date(d);
  x.setDate(x.getDate() + days);
  return x;
}
function ymdLocal(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}
function fmtDateOnly(val){
  if (!val) return "";
  const d = new Date(val);
  if (!isNaN(d)) {
    return d.toLocaleDateString(undefined, {
      weekday: "short", year: "numeric", month: "short", day: "2-digit"
    });
  }
  // fallback: strip trailing midnight like " 00:00", " 00:00:00 GMT"
  if (typeof val === "string") {
    return val.replace(/\s+00:00(?::00)?(?:\s*GMT)?$/i, "");
  }
  return String(val);
}

export default function ResultsTab(){
  // Default range = past 7 days (today minus 6 through today)
  const today = new Date();
  const defaultTo = ymdLocal(today);
  const defaultFrom = ymdLocal(addDays(today, -6));

  const [from, setFrom] = useState(defaultFrom);
  const [to, setTo] = useState(defaultTo);
  const [items, setItems] = useState([]);
  const [err, setErr] = useState(null);

  const load = async () => {
    setErr(null);
    try {
      const qs = new URLSearchParams({ ...(from && { from }), ...(to && { to }) });
      const data = await api(`/api/results${qs.toString() ? "?" + qs.toString() : ""}`);
      setItems(data.results || []);
    } catch (ex) {
      setErr(ex?.data?.error || ex.message);
    }
  };

  // Initial load with the default 7-day range
  useEffect(() => { load(); }, []); 

  function fmtScore(m){
    return (m.home_score != null && m.away_score != null)
      ? `${m.home_score}-${m.away_score}`
      : "-";
  }

  return (
    <Card>
      <div className="flex flex-wrap items-end gap-3 mb-3">
        <div>
          <label className="block text-sm mb-1">From</label>
          <input
            type="date"
            className="border border-zinc-300 rounded-xl px-3 py-2"
            value={from}
            onChange={e=>setFrom(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm mb-1">To</label>
          <input
            type="date"
            className="border border-zinc-300 rounded-xl px-3 py-2"
            value={to}
            onChange={e=>setTo(e.target.value)}
          />
        </div>
        <button onClick={load} className="px-3 py-2 rounded-xl bg-zinc-900 text-white">
          Refresh
        </button>
      </div>

      {err && <div className="text-sm text-red-600 mb-2">{err}</div>}

      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-zinc-500 border-b">
            <th className="py-2">Date</th>
            <th>Time</th>
            <th>Match</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {items.length === 0 ? (
            <tr>
              <td className="py-3 text-zinc-500" colSpan={4}>No results found for this period.</td>
            </tr>
          ) : (
            items.map((m, i) => (
              <tr key={ i } className="border-b last:border-0">
                <td className="py-2 whitespace-nowrap">{fmtDateOnly(m.date)}</td>
                <td className="whitespace-nowrap">{m.time || ""}</td>
                <td>{m.home} vs {m.away}</td>
                <td>{fmtScore(m)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </Card>
  );
}