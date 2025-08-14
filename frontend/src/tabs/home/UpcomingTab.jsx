import React, { useEffect, useState } from "react";
import Card from "../../components/Card.jsx";
import { api } from "../../lib/api.js";

export default function UpcomingTab(){
  const [items, setItems] = useState([]);
  const [err, setErr] = useState(null);

  useEffect(() => { (async()=>{
    try { const data = await api("/api/upcoming"); setItems(data.items || []); }
    catch(ex){ setErr(ex?.data?.error || ex.message); }
  })(); }, []);

  // ---- helpers ----
  function fmtDateOnly(val){
    if (!val) return "";
    // Try to parse and format as a pure date (no timezone text)
    const d = new Date(val);
    if (!isNaN(d)) {
      return d.toLocaleDateString(undefined, {
        weekday: "short", year: "numeric", month: "short", day: "2-digit"
      });
    }
    // Fallback: strip common trailing midnight strings like " 00:00", " 00:00:00 GMT"
    if (typeof val === "string") {
      return val.replace(/\s+00:00(?::00)?(?:\s*GMT)?$/i, "");
    }
    return String(val);
  }

  return (
    <Card>
      <h2 className="font-semibold mb-3">Next matches</h2>
      {err && <div className="text-sm text-red-600 mb-2">{err}</div>}
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-zinc-500 border-b">
            <th className="py-2">Date</th>
            <th>Time</th>
            <th>Match</th>
          </tr>
        </thead>
        <tbody>
          {items.map((m) => (
            <tr key={m.match_id} className="border-b last:border-0">
              <td className="py-2 whitespace-nowrap">{fmtDateOnly(m.date)}</td>
              <td className="whitespace-nowrap">{m.time}</td>
              <td>{m.home} vs {m.away}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}