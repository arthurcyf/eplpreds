import React, { useEffect, useState } from "react";
import Card from "../../components/Card.jsx";
import NumberInput from "../../components/NumberInput.jsx";
import { api } from "../../lib/api.js";

export default function PredictionsTab({ groupId }){
  const [scope, setScope] = useState("current"); // current | next
  const [windowInfo, setWindowInfo] = useState(null);
  const [matches, setMatches] = useState([]);
  const [timeById, setTimeById] = useState({});   // match_id -> "HH:MM"
  const [picks, setPicks] = useState({});
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
      const list = data.matches || [];
      setMatches(list);

      // prefill picks from server
      const seed = {};
      for (const m of list) {
        if (m.my_home_pred != null || m.my_away_pred != null) {
          seed[m.match_id] = { home_pred: m.my_home_pred ?? "", away_pred: m.my_away_pred ?? "" };
        }
      }
      setPicks(seed);

      // hydrate times from /api/upcoming (where m.time is known to exist)
      await hydrateTimes(list);
    } catch (ex) {
      setMsg(ex?.data?.error || ex.message);
    }
  };
  useEffect(()=>{ loadMatches(); }, [groupId, scope]);

  const savePreds = async () => {
    setSaving(true); setMsg(null);
    try {
      const predictions = Object.entries(picks).map(([match_id, v]) => ({
        match_id, home_pred: +v.home_pred, away_pred: +v.away_pred
      }));
      const res = await api(`/groups/${groupId}/predictions?scope=${scope}`, { method: "POST", body: { predictions } });
      setMsg(`Saved ${res.saved} prediction(s).`);
      await loadMatches();
      await tryLoadOthers();
    } catch (ex) {
      setMsg(ex?.data?.error || ex.message);
    } finally {
      setSaving(false);
    }
  };

  const tryLoadOthers = async () => {
    try { const o = await api(`/groups/${groupId}/predictions/others?scope=${scope}`); setOthers(o); }
    catch (ex) { setOthers({ error: ex?.data?.error || ex.message }); }
    try { const s = await api(`/groups/${groupId}/predictions/stats`); setStats(s); }
    catch (ex) { setStats({ error: ex?.data?.error || ex.message }); }
  };
  useEffect(()=>{ tryLoadOthers(); }, [groupId, scope]);

  // -------- Time helpers --------
  function pickKickoff(m){
    return m.local_kickoff ?? m.kickoff_local ?? m.utc_kickoff ?? m.kickoff_utc ??
           m.kickoff ?? m.kickoff_at ?? m.datetime ?? m.date_time ??
           m.ts ?? m.timestamp ?? null;
  }
  function deriveTime(m){
    // If backend actually sent time, use it
    if (m.time) return m.time;
    const ko = pickKickoff(m);
    if (!ko) return "";
    const d = new Date(ko);
    if (isNaN(d)) return "";
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false });
  }
  async function hydrateTimes(list){
    try {
      const upcoming = await api("/api/upcoming");
      const items = upcoming.items || [];
      const map = {};
      const needed = new Set(list.map(x => String(x.match_id)));
      for (const it of items) {
        const id = String(it.match_id);
        if (!needed.has(id)) continue;
        map[id] = it.time || deriveTime(it) || "";
      }
      // Fill any gaps with local derivation from the predictions payload itself
      for (const m of list) {
        const id = String(m.match_id);
        if (!map[id]) map[id] = deriveTime(m);
      }
      setTimeById(map);
    } catch {
      // Fallback: derive directly from predictions payload only
      const map = {};
      for (const m of list) map[String(m.match_id)] = deriveTime(m);
      setTimeById(map);
    }
  }

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
                <th className="py-2">Time</th>
                <th>Match</th>
                <th className="text-center">Your pick</th>
              </tr>
            </thead>
            <tbody>
              {matches.map(m => (
                <tr key={m.match_id} className="border-b last:border-0">
                  <td className="py-2 align-top whitespace-nowrap">{m.date}</td>
                  <td className="py-2 align-top whitespace-nowrap">{timeById[String(m.match_id)] ?? ""}</td>
                  <td className="py-2 align-top whitespace-nowrap">{m.home} vs {m.away}</td>
                  <td className="py-2 align-top whitespace-nowrap">
                    <div className="flex items-center gap-2 justify-center">
                      <NumberInput
                        value={picks[m.match_id]?.home_pred}
                        onChange={(v)=>setPicks(p=>({ ...p, [m.match_id]: { ...(p[m.match_id]||{}), home_pred: v } }))}
                        placeholder="H"
                      />
                      <span className="text-zinc-500">-</span>
                      <NumberInput
                        value={picks[m.match_id]?.away_pred}
                        onChange={(v)=>setPicks(p=>({ ...p, [m.match_id]: { ...(p[m.match_id]||{}), away_pred: v } }))}
                        placeholder="A"
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-3 flex justify-end">
          <button disabled={saving} onClick={savePreds} className="px-3 py-2 rounded-xl bg-zinc-900 text-white disabled:opacity-50">
            {saving ? "Saving…" : "Save predictions"}
          </button>
        </div>
      </Card>

      <div className="space-y-4">
        <Card>
          <h3 className="font-semibold mb-2">Others' picks</h3>
          {others?.error && <div className="text-sm text-zinc-500">{others.error}</div>}
          {others?.predictions?.length ? others.predictions.map(p => (
            <div key={`${p.match_id}-${p.username ?? p.email}`} className="text-sm border-t first:border-t-0 py-2">
              <div className="font-medium">{p.home} vs {p.away}</div>
              <div className="text-zinc-500">{p.username ? `@${p.username}` : p.email}: {p.home_pred}-{p.away_pred}</div>
            </div>
          )) : <div className="text-sm text-zinc-500">No one has submitted yet.</div>}
        </Card>

        <Card>
          <h3 className="font-semibold mb-2">Stats</h3>
          {stats?.error && <div className="text-sm text-zinc-500">{stats.error}</div>}
          {stats?.matches && stats.matches.map(m => (
            <div key={m.match_id} className="text-sm border-t first:border-t-0 py-2">
              <div className="font-medium">{m.home} vs {m.away}</div>
              <div className="text-zinc-500">
                Outcome votes — Home: {m.outcomes?.home || 0}, Draw: {m.outcomes?.draw || 0}, Away: {m.outcomes?.away || 0}
              </div>
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
      <span className={`px-2 py-1 rounded-full ${cur.open ? "bg-emerald-50 text-emerald-700" : "bg-zinc-100"}`}>
        Current: {cur.start} → {cur.end}
      </span>
      <span className={`px-2 py-1 rounded-full ${nxt.open ? "bg-emerald-50 text-emerald-700" : "bg-zinc-100"}`}>
        Next: {nxt.start} → {nxt.end}
      </span>
    </div>
  );
}