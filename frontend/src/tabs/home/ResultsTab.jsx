import React, { useEffect, useState } from "react";
import Card from "../../components/Card.jsx";
import { api } from "../../lib/api.js";

export default function ResultsTab(){
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [items, setItems] = useState([]);
  const [err, setErr] = useState(null);

  const load = async () => {
    setErr(null);
    try {
      const qs = new URLSearchParams({ ...(from && { from }), ...(to && { to }) });
      const data = await api(`/api/results${qs.toString()?"?"+qs.toString():""}`);
      setItems(data.results || []);
    } catch (ex) { setErr(ex?.data?.error || ex.message); }
  };
  useEffect(()=>{ load(); }, []);

  return (
    <Card>
      <div className="flex flex-wrap items-end gap-3 mb-3">
        <div>
          <label className="block text-sm mb-1">From</label>
          <input type="date" className="border border-zinc-300 rounded-xl px-3 py-2" value={from} onChange={e=>setFrom(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm mb-1">To</label>
          <input type="date" className="border border-zinc-300 rounded-xl px-3 py-2" value={to} onChange={e=>setTo(e.target.value)} />
        </div>
        <button onClick={load} className="px-3 py-2 rounded-xl bg-zinc-900 text-white">Refresh</button>
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
          {items.map((m, i) => (
            <tr key={i} className="border-b last:border-0">
              <td className="py-2">{m.date}</td>
              <td>{m.time}</td>
              <td>{m.home} vs {m.away}</td>
              <td>{m.home_score != null ? `${m.home_score}-${m.away_score}` : "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}