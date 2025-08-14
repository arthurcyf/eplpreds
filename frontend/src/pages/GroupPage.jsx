import React, { useState, useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import Tabs from "../components/Tabs.jsx";
import PredictionsTab from "../tabs/group/PredictionsTab.jsx";
import LeaderboardTab from "../tabs/group/LeaderboardTab.jsx";
import GroupSettingsTab from "../tabs/group/GroupSettingsTab.jsx"; // rename file or export default
import { api } from "../lib/api.js";

export default function GroupPage(){
  const { id } = useParams();
  const [tab, setTab] = useState("Predictions");
  const [group, setGroup] = useState(null);

  useEffect(() => { (async ()=>{
    try { const g = await api(`/groups/${id}`); setGroup(g); }
    catch(e){ /* handle 403/404 */ }
  })(); }, [id]);

  const tabs = ["Predictions","Leaderboard", ...(group?.is_admin ? ["Group Settings"] : [])];

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-xl font-semibold">{group?.name ?? `Group #${id}`}</h1>
        <Link to="/" className="text-sm text-zinc-500 hover:text-zinc-800">← Back</Link>
      </div>
      <Tabs tabs={tabs} value={tab} onChange={setTab} />
      <div className="mt-4">
        {tab === "Predictions" && <PredictionsTab groupId={+id} />}
        {tab === "Leaderboard" && <LeaderboardTab groupId={+id} />}
        {tab === "Group Settings" && group?.is_admin && <GroupSettingsTab groupId={+id} />}
      </div>
    </div>
  );
}
