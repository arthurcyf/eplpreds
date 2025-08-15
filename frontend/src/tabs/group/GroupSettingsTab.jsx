import React, { useEffect, useState } from "react";
import Card from "../../components/Card.jsx";
import { api } from "../../lib/api.js";

export default function GroupSettingsTab({ groupId }) {
  const [group, setGroup] = useState(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [joinPolicy, setJoinPolicy] = useState("invite_only");
  const [msg, setMsg] = useState(null);
  const [pending, setPending] = useState([]);
  const [err, setErr] = useState(null);

  // load basic group info (incl. invite_code, is_admin)
  useEffect(() => {
    api(`/groups/${groupId}`).then(setGroup).catch(() => {});
  }, [groupId]);

  const loadRequests = async () => {
    setErr(null);
    try {
      const res = await api(`/groups/${groupId}/requests`);
      setPending(res.pending || []);
    } catch (ex) {
      setErr(ex?.data?.error || ex.message);
    }
  };
  useEffect(() => {
    loadRequests();
  }, [groupId]);

  const save = async (e) => {
    e.preventDefault();
    setMsg(null);
    try {
      await api(`/groups/${groupId}/settings`, {
        method: "POST",
        body: {
          ...(name && { name }),
          description,
          is_public: isPublic,
          join_policy: joinPolicy,
        },
      });
      setMsg("Settings saved.");
      // refresh header info (in case name/policy/code changed server-side)
      api(`/groups/${groupId}`).then(setGroup).catch(() => {});
    } catch (ex) {
      setMsg(ex?.data?.error || ex.message);
    }
  };

  const act = async (user_id, action) => {
    try {
      await api(`/groups/${groupId}/requests/${user_id}`, {
        method: "POST",
        body: { action },
      });
      setPending(pending.filter((p) => p.user_id !== user_id));
    } catch (ex) {
      setMsg(ex?.data?.error || ex.message);
    }
  };

  const [members, setMembers] = useState([]);
  const loadMembers = async () => {
    try {
      const res = await api(`/groups/${groupId}/members`);
      setMembers(res.members || []);
    } catch (ex) {
      setMsg(ex?.data?.error || ex.message);
    }
  };
  useEffect(() => {
    loadMembers();
  }, [groupId]);

  async function toggleAdmin(u) {
    try {
      await api(`/groups/${groupId}/members/${u.user_id}/role`, {
        method: "POST",
        body: { is_admin: !u.is_admin },
      });
      setMembers(
        members.map((m) =>
          m.user_id === u.user_id ? { ...m, is_admin: !u.is_admin } : m
        )
      );
    } catch (ex) {
      setMsg(ex?.data?.error || ex.message);
    }
  }

  const inviteLink =
    group?.invite_code ? `${window.location.origin}/join/${group.invite_code}` : "";

  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <Card className="lg:col-span-2">
        {/* Header + Invite code badge */}
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Group settings</h2>
          {group?.invite_code && (
            <div className="text-xs flex items-center gap-2">
              <span className="text-zinc-500">Code:</span>
              <span className="font-mono">{group.invite_code}</span>
              <button
                type="button"
                className="px-3 py-2 rounded-xl bg-zinc-900 text-white"
                onClick={() => navigator.clipboard.writeText(group.invite_code)}
              >
                Copy code
              </button>
            </div>
          )}
        </div>

        {msg && <div className="text-sm text-zinc-600 mb-2">{msg}</div>}

        <form onSubmit={save} className="grid gap-3 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="block text-sm mb-1">Name</label>
            <input
              className="w-full border border-zinc-300 rounded-xl px-3 py-2"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="(leave blank to keep)"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm mb-1">Description</label>
            <textarea
              className="w-full border border-zinc-300 rounded-xl px-3 py-2"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your group"
            />
          </div>
          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={isPublic}
              onChange={(e) => {
                setIsPublic(e.target.checked);
                setJoinPolicy(e.target.checked ? "public" : "invite_only");
              }}
            />{" "}
            Public group
          </label>
          <div>
            <label className="block text-sm mb-1">Join policy</label>
            <select
              value={joinPolicy}
              onChange={(e) => setJoinPolicy(e.target.value)}
              className="px-3 py-2 rounded-xl bg-zinc-900 text-white"
            >
              <option value="invite_only">Invite Only</option>
              <option value="public">Public</option>
            </select>
          </div>
          <div className="md:col-span-2 mt-1">
            <button className="px-3 py-2 rounded-xl bg-zinc-900 text-white">
              Save
            </button>
          </div>
        </form>
        <div className="text-xs text-zinc-500 mt-2">
          Only the group owner can modify settings. If you're not the owner,
          actions will be rejected.
        </div>
      </Card>

      <Card>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold">Join requests</h3>
          <button
            onClick={loadRequests}
            className="px-3 py-2 rounded-xl bg-zinc-900 text-white"
          >
            Reload
          </button>
        </div>
        {err && <div className="text-sm text-red-600 mb-2">{err}</div>}
        {pending.length === 0 ? (
          <div className="text-sm text-zinc-500">No pending requests.</div>
        ) : (
          <div className="space-y-2">
            {pending.map((p) => (
              <div
                key={p.user_id}
                className="border border-zinc-200 rounded-xl p-3 text-sm"
              >
                <div className="font-medium">{p.email}</div>
                <div className="text-zinc-500 mb-2">
                  Requested at {new Date(p.requested_at).toLocaleString()}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => act(p.user_id, "approve")}
                    className="px-3 py-1.5 rounded-xl bg-emerald-600 text-white"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => act(p.user_id, "reject")}
                    className="px-3 py-1.5 rounded-xl bg-rose-600 text-white"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold">Members</h3>
          <button onClick={loadMembers} className="px-2 py-1 rounded-lg border">
            Reload
          </button>
        </div>
        <div className="space-y-2 text-sm">
          {members.map((m) => (
            <div
              key={m.user_id}
              className="flex items-center justify-between border rounded-xl p-3"
            >
              <div>
                <div className="font-medium">
                  {m.username ? `@${m.username}` : m.email}
                </div>
                <div className="text-xs text-zinc-500">
                  {m.status}
                  {m.is_admin ? " · admin" : ""}
                </div>
              </div>
              <button
                onClick={() => toggleAdmin(m)}
                className="px-3 py-2 rounded-xl bg-zinc-900 text-white"
              >
                {m.is_admin ? "Remove admin" : "Make admin"}
              </button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}