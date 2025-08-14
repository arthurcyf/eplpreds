import React, { useEffect, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../lib/api.js";

export default function AccountMenu(){
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [showChangePw, setShowChangePw] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onDocClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const label = user?.username ? `@${user.username}` : (user?.email || "Account");

  return (
    <div ref={ref} className="relative">
      <button
        className="text-sm underline text-zinc-700 hover:text-black"
        onClick={() => setOpen(o => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        {label}
      </button>

      {open && (
        <div role="menu" className="absolute right-0 mt-2 w-44 rounded-xl border bg-white shadow-lg p-1 z-50">
          <button
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-100"
            onClick={() => { setOpen(false); setShowChangePw(true); }}
          >
            Change password
          </button>
          <button
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-100 text-zinc-600"
            onClick={logout}
          >
            Logout
          </button>
        </div>
      )}

      {showChangePw && <ChangePasswordModal onClose={() => setShowChangePw(false)} />}
    </div>
  );
}

function ChangePasswordModal({ onClose }){
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [newPw2, setNewPw2] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [ok, setOk] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setErr(null); setOk(null);

    if (newPw !== newPw2) { setErr("New passwords do not match."); return; }
    if (newPw.length < 8) { setErr("Password must be at least 8 characters."); return; }

    setBusy(true);
    try {
      await api("/auth/password", { method: "POST", body: { old_password: oldPw, new_password: newPw } });
      setOk("Password updated.");
      setOldPw(""); setNewPw(""); setNewPw2("");
      setTimeout(onClose, 900);
    } catch (ex) {
      setErr(ex?.data?.error || ex.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-4 shadow-xl">
        <h3 className="text-lg font-semibold mb-3">Change password</h3>
        {err && <div className="text-sm text-rose-600 mb-2">{err}</div>}
        {ok && <div className="text-sm text-emerald-700 mb-2">{ok}</div>}

        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="block text-sm mb-1">Current password</label>
            <input
              type="password"
              className="w-full border border-zinc-300 rounded-xl px-3 py-2"
              value={oldPw}
              onChange={e=>setOldPw(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm mb-1">New password</label>
            <input
              type="password"
              className="w-full border border-zinc-300 rounded-xl px-3 py-2"
              value={newPw}
              onChange={e=>setNewPw(e.target.value)}
              required
              minLength={8}
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Confirm new password</label>
            <input
              type="password"
              className="w-full border border-zinc-300 rounded-xl px-3 py-2"
              value={newPw2}
              onChange={e=>setNewPw2(e.target.value)}
              required
              minLength={8}
            />
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="px-3 py-2 rounded-xl border">
              Cancel
            </button>
            <button disabled={busy} className="px-3 py-2 rounded-xl bg-zinc-900 text-white disabled:opacity-50">
              {busy ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}