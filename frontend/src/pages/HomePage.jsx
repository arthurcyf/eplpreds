import React, { useState } from "react";
import Tabs from "../components/Tabs.jsx";
import GroupsTab from "../tabs/home/GroupsTab.jsx";
import UpcomingTab from "../tabs/home/UpcomingTab.jsx";
import ResultsTab from "../tabs/home/ResultsTab.jsx";

export default function HomePage(){
  const [tab, setTab] = useState("Groups");
  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <Tabs tabs={["Groups","Upcoming matches","Results"]} value={tab} onChange={setTab} />
      <div className="mt-4">
        {tab === "Groups" && <GroupsTab />}
        {tab === "Upcoming matches" && <UpcomingTab />}
        {tab === "Results" && <ResultsTab />}
      </div>
    </div>
  );
}