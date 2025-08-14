import React, { useEffect, useState } from "react";
import Card from "../../components/Card.jsx";
import NumberInput from "../../components/NumberInput.jsx";
import { api } from "../../lib/api.js";
import { fmtRange, fmtTime } from "../../utils/format.js";

export default function PredictionsTab({ groupId }){
  const [scope, setScope] = useState("current"); // current | next
  const [windowInfo, setWindowInfo] = useState(null);
  const [matches, setMatches] = useState([]);
  const [picks, setPicks] = useState({}); // match_id -> {home_pred, away_pred}
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);
  const [others, setOthers] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => { (async()=>{
    try { const w = await api(`/groups/${groupId}/predictions/window`); setWindowInfo(w); } catch {}
  })(); }, [groupId]);

  const loadMatches = async () => {
    setMsg(null);
    try {
      const data = await api(`/groups/${groupId}/predictions/matches?scope=${scope}`);
      setMatches(data.matches || []);
    } catch (ex) { setMsg(ex?.data?.error || ex.message); }
  };
  useEffect(()=>{ loadMatches(); }, [groupId, scope]);

  const savePreds = async () => {
    setSaving(true); setMsg(null);
    try {
      const predictions = Object.entries(picks).map(([match_id, v]) => ({ match_id, home_pred: +v.home_pred, away_pred: +v.away_pred }));
      const res = await api(`/groups/${groupId}/predictions?scope=${scope}`, { method: "POST", body: { predictions } });
      setMsg(`Saved ${res.saved} prediction(s).`);
    } catch (ex) { setMsg(ex?.data?.error || ex.message); }
    finally { setSaving(false); }
  };

  const tryLoadOthers = async () => {
    try { const o = await api(`/groups/${groupId}/predictions/others`); setOthers(o); } catch (ex) { setOthers({ error: ex?.data?.error || ex.message }); }
    try { const s = await api(`/groups/${groupId}/predictions/stats`); setStats(s); } catch (ex) { setStats({ error: ex?.data?.error || ex.message }); }
  };
  useEffect(()=>{ tryLoadOthers(); }, [groupId]);

  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <Card className="lg:col-span-2">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Your predictions</h2>
          <div className="flex items-center gap-2 text-sm">
            <label className="text-zinc-500">Scope:</label>
            <select value={scope} onChange={e=>setScope(e.target.value)} className="border border-zinc-300 rounded-lg px-2 py-1">
              <option value="current">Current window</option>
              <option value="next">Next window</option>
            </select>
            <button onClick={loadMatches} className="px-2 py-1 rounded-lg border">Reload</button>
          </div>
        </div>
        {windowInfo && <WindowInfo info={windowInfo} />}
        {msg && <div className="text-sm text-zinc-600 mb-2">{msg}</div>}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-500 border-b">
                <th className="py-2">Date</th>
                <th>Match</th>
                <th className="text-center">Your pick</th>
              </tr>
            </thead>
            <tbody>
              {matches.map(m => (
                <tr key={m.match_id} className="border-b last:border-0">
                  <td className="py-2 align-top whitespace-nowrap">{m.date} {m.time}</td>
                  <td className="align-top">{m.home} vs {m.away}</td>
                  <td className="align-top">
                    <div className="flex items-center gap-2 justify-center">
                      <NumberInput
                        value={picks[m.match_id]?.home_pred}
                        onChange={(v)=>setPicks(p=>({ ...p, [m.match_id]: { ...(p[m.match_id]||{}), home_pred: v } }))}
                        placeholder="H"/>
                      <span className="text-zinc-500">-</span>
                      <NumberInput
                        value={picks[m.match_id]?.away_pred}
                        onChange={(v)=>setPicks(p=>({ ...p, [m.match_id]: { ...(p[m.match_id]||{}), away_pred: v } }))}
                        placeholder="A"/>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex justify-end">
          <button disabled={saving} onClick={savePreds} className="px-3 py-2 rounded-xl bg-zinc-900 text-white disabled:opacity-50">{saving?"Saving…":"Save predictions"}</button>
        </div>
      </Card>

      <div className="space-y-4">
        <Card>
          <h3 className="font-semibold mb-2">Others' picks</h3>
          {others?.error && <div className="text-sm text-zinc-500">{others.error}</div>}
          {!others?.items && !others?.error && <div className="text-sm text-zinc-500">Not available until the window closes.</div>}
          {others?.items && others.items.map(item => (
            <div key={item.match_id} className="text-sm border-t first:border-t-0 py-2">
              <div className="font-medium">{item.home} vs {item.away}</div>
              <div className="text-zinc-500">{item.predictions.length} picks</div>
            </div>
          ))}
        </Card>
        <Card>
          <h3 className="font-semibold mb-2">Stats</h3>
          {stats?.error && <div className="text-sm text-zinc-500">{stats.error}</div>}
          {stats?.matches && stats.matches.map(m => (
            <div key={m.match_id} className="text-sm border-t first:border-t-0 py-2">
              <div className="font-medium">{m.home} vs {m.away}</div>
              <div className="text-zinc-500">Outcome votes — Home: {m.outcomes.home || 0}, Draw: {m.outcomes.draw || 0}, Away: {m.outcomes.away || 0}</div>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

function WindowInfo({ info }){
  const cur = info.current; const nxt = info.next;
  return (
    <div className="flex flex-wrap gap-3 text-xs text-zinc-600 mb-3">
      <span className={`px-2 py-1 rounded-full ${cur.open?"bg-emerald-50 text-emerald-700":"bg-zinc-100"}`}>Current: {fmtRange(cur.start, cur.end)} · Open {fmtTime(cur.open_at)} → Close {fmtTime(cur.close_at)} {cur.open?"(OPEN)":"(CLOSED)"}</span>
      <span className={`px-2 py-1 rounded-full ${nxt.open?"bg-emerald-50 text-emerald-700":"bg-zinc-100"}`}>Next: {fmtRange(nxt.start, nxt.end)} · Open {fmtTime(nxt.open_at)} → Close {fmtTime(nxt.close_at)} {nxt.open?"(OPEN)":""}</span>
    </div>
  );
}