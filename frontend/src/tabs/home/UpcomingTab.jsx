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
              <td className="py-2">{m.date}</td>
              <td>{m.time}</td>
              <td>{m.home} vs {m.away}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}