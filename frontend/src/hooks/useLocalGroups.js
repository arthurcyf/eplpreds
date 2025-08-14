import { useEffect, useState } from "react";
export default function useLocalGroups(){
  const key = "epl_my_groups";
  const [groups, setGroups] = useState(() => {
    try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch { return []; }
  });
  useEffect(() => { localStorage.setItem(key, JSON.stringify(groups)); }, [groups]);
  return [groups, setGroups];
}