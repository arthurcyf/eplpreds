import React, { useEffect, useState } from "react";
import Card from "../../components/Card.jsx";
import { api } from "../../lib/api.js";

export default function LeaderboardTab({ groupId }) {
  const [rows, setRows] = useState([]);
  const [high, setHigh] = useState(null);
  const [err, setErr] = useState(null);

  const load = async () => {
    setErr(null);
    try {
      const lb = await api(`/groups/${groupId}/leaderboard`);
      const hi = await api(`/groups/${groupId}/leaderboard/highlights`);
      setRows(lb.leaderboard || []);
      setHigh(hi);
    } catch (ex) {
      setErr(ex?.data?.error || ex.message);
    }
  };
  useEffect(() => {
    load();
  }, [groupId]);

  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <Card className="lg:col-span-2">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Leaderboard</h2>
          <button onClick={load} className="px-2 py-1 rounded-lg border">
            Refresh
          </button>
        </div>
        {err && <div className="text-sm text-red-600 mb-2">{err}</div>}
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-zinc-500 border-b">
              <th className="py-2">#</th>
              <th>User</th>
              <th>Total points</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.user_id} className="border-b last:border-0">
                <td className="py-2">{i + 1}</td>
                <td>
                  {r.username ? `@${r.username}` : r.email ?? `#${r.user_id}`}
                </td>

                <td>{r.total_points}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card>
        <h3 className="font-semibold mb-2">Highlights</h3>
        {high && (
          <div className="space-y-2 text-sm">
            <div className="text-zinc-500">Week starting {high.week_start}</div>
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200">
              <div className="font-medium">Best performer</div>
              {high.best ? (
                <div>
                  User #{high.best.user_id} · {high.best.points} pts
                </div>
              ) : (
                <div>-</div>
              )}
            </div>
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200">
              <div className="font-medium">Tough week</div>
              {high.worst ? (
                <div>
                  User #{high.worst.user_id} · {high.worst.points} pts
                </div>
              ) : (
                <div>-</div>
              )}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
