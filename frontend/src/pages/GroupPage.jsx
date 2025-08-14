import React, { useState } from "react";
import { Link, useParams } from "react-router-dom";
import Tabs from "../components/Tabs.jsx";
import PredictionsTab from "../tabs/group/PredictionsTab.jsx";
import LeaderboardTab from "../tabs/group/LeaderboardTab.jsx";
import AdminTab from "../tabs/group/AdminTab.jsx";

export default function GroupPage(){
  const { id } = useParams();
  const [tab, setTab] = useState("Predictions");
  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-xl font-semibold">Group #{id}</h1>
        <Link to="/" className="text-sm text-zinc-500 hover:text-zinc-800">← Back</Link>
      </div>
      <Tabs tabs={["Predictions","Leaderboard","Admin"]} value={tab} onChange={setTab} />
      <div className="mt-4">
        {tab === "Predictions" && <PredictionsTab groupId={+id} />}
        {tab === "Leaderboard" && <LeaderboardTab groupId={+id} />}
        {tab === "Admin" && <AdminTab groupId={+id} />}
      </div>
    </div>
  );
}