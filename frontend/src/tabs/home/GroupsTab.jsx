import React, { useState } from "react";
import Card from "../../components/Card.jsx";
import { Link } from "react-router-dom";
import { api } from "../../lib/api.js";
import useLocalGroups from "../../hooks/useLocalGroups.js";

export default function GroupsTab(){
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [joinCode, setJoinCode] = useState("");
  const [msg, setMsg] = useState(null);
  const [myGroups, setMyGroups] = useLocalGroups();

  const createGroup = async (e) => {
    e.preventDefault(); setMsg(null);
    try {
      const res = await api("/groups", { method: "POST", body: { name, description, is_public: isPublic } });
      const g = { id: res.group_id, name: name || "My Group", code: res.invite_code };
      setMyGroups([g, ...myGroups]);
      setName(""); setDescription(""); setIsPublic(false);
      setMsg(`Created group #${res.group_id}`);
    } catch (ex) { setMsg(ex?.data?.error || ex.message); }
  };

  const joinByCode = async (e) => {
    e.preventDefault(); setMsg(null);
    try {
      const res = await api("/groups/join", { method: "POST", body: { code: joinCode } });
      const g = { id: res.group_id, name: res.group_name, code: joinCode };
      setMyGroups([g, ...myGroups.filter(x => x.id !== g.id)]);
      setJoinCode("");
      setMsg(`Joined ${res.group_name} (${res.status})`);
    } catch (ex) { setMsg(ex?.data?.error || ex.message); }
  };

  return (
    <div className="grid md:grid-cols-3 gap-4">
      <Card className="md:col-span-2">
        <h2 className="font-semibold mb-2">Create a group</h2>
        <form onSubmit={createGroup} className="grid gap-3 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="block text-sm mb-1">Name</label>
            <input className="w-full border border-zinc-300 rounded-xl px-3 py-2" value={name} onChange={e=>setName(e.target.value)} placeholder="My EPL Group" />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm mb-1">Description</label>
            <textarea className="w-full border border-zinc-300 rounded-xl px-3 py-2" value={description} onChange={e=>setDescription(e.target.value)} placeholder="Friends, family, colleagues…" />
          </div>
          <label className="inline-flex items-center gap-2"><input type="checkbox" checked={isPublic} onChange={e=>setIsPublic(e.target.checked)} /> Public group</label>
          <div className="md:col-span-2 mt-1">
            <button className="px-3 py-2 rounded-xl bg-zinc-900 text-white">Create</button>
          </div>
        </form>
      </Card>

      <Card>
        <h2 className="font-semibold mb-2">Join by code</h2>
        <form onSubmit={joinByCode} className="space-y-3">
          <input className="w-full border border-zinc-300 rounded-xl px-3 py-2" value={joinCode} onChange={e=>setJoinCode(e.target.value)} placeholder="Invite code" />
          <button className="w-full py-2 rounded-xl bg-zinc-900 text-white">Join</button>
        </form>
      </Card>

      <div className="md:col-span-3">
        {msg && <div className="mb-3 text-sm text-zinc-600">{msg}</div>}
        <Card>
          <h2 className="font-semibold mb-3">My groups</h2>
          {myGroups.length === 0 ? (
            <div className="text-sm text-zinc-500">You haven't joined/created any groups yet.</div>
          ) : (
            <div className="grid md:grid-cols-2 gap-3">
              {myGroups.map(g => <GroupCard key={g.id} group={g} />)}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

function GroupCard({ group }){
  return (
    <div className="border border-zinc-200 rounded-2xl p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium">{group.name || `Group #${group.id}`}</div>
          {group.code && <div className="text-xs text-zinc-500">Invite: {group.code}</div>}
        </div>
        <Link to={`/group/${group.id}`} className="px-3 py-1.5 rounded-xl bg-zinc-900 text-white">Open</Link>
      </div>
    </div>
  );
}