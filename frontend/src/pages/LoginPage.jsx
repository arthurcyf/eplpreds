import React, { useState } from "react";
import Card from "../components/Card.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useNavigate } from "react-router-dom";

const USERNAME_RE = /^[a-z0-9_]{3,20}$/;

export default function LoginPage(){
  const { login, register, setUsername } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUname] = useState("");
  const [mode, setMode] = useState("login");
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);

    try {
      if (mode === "register") {
        // basic client-side username validation to give fast feedback
        const uname = username.trim().toLowerCase();
        if (!USERNAME_RE.test(uname)) {
          setErr("Username must be 3–20 characters: a–z, 0–9, underscore.");
          setLoading(false);
          return;
        }

        // 1) create account
        await register(email, password); // your existing API call
        // 2) login
        await login(email, password);
        // 3) set username (server enforces uniqueness and format too)
        await setUsername(uname);

        // success — head home
        nav("/");
        return;
      }

      // login mode
      await login(email, password);
      nav("/");
    } catch (ex) {
      setErr(ex?.data?.error || ex.message);
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(mode === "login" ? "register" : "login");
    setErr(null);
  };

  return (
    <div className="min-h-screen grid place-items-center bg-zinc-50">
      <Card className="w-full max-w-md">
        <h1 className="text-xl font-semibold mb-2">
          {mode === "login" ? "Login" : "Create an account"}
        </h1>
        <p className="text-sm text-zinc-500 mb-4">Use your email & password.</p>

        {err && <div className="mb-3 text-red-600 text-sm">{err}</div>}

        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="block text-sm mb-1">Email</label>
            <input
              className="w-full border border-zinc-300 rounded-xl px-3 py-2"
              type="email"
              value={email}
              onChange={e=>setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-sm mb-1">Password</label>
            <input
              className="w-full border border-zinc-300 rounded-xl px-3 py-2"
              type="password"
              value={password}
              onChange={e=>setPassword(e.target.value)}
              required
            />
          </div>

          {mode === "register" && (
            <div>
              <label className="block text-sm mb-1">Username</label>
              <input
                className="w-full border border-zinc-300 rounded-xl px-3 py-2"
                type="text"
                placeholder="e.g. footy_ace"
                value={username}
                onChange={e=>setUname(e.target.value)}
                required
              />
              <div className="text-xs text-zinc-500 mt-1">
                3–20 chars, a–z, 0–9, underscore. Must be unique.
              </div>
            </div>
          )}

          <button
            className="w-full py-2 rounded-xl bg-zinc-900 text-white disabled:opacity-60"
            disabled={loading}
          >
            {loading
              ? "Please wait…"
              : mode==="login" ? "Login" : "Register & Login"}
          </button>
        </form>

        <div className="text-sm text-zinc-500 mt-4">
          {mode === "login" ? (
            <button className="underline" onClick={switchMode}>
              No account? Register
            </button>
          ) : (
            <button className="underline" onClick={switchMode}>
              Have an account? Login
            </button>
          )}
        </div>
      </Card>
    </div>
  );
}