import React, { useState } from "react";
import Card from "../components/Card.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useNavigate } from "react-router-dom";

export default function LoginPage(){
  const { login, register } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("login");
  const [err, setErr] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setErr(null);
    try {
      if (mode === "register") { await register(email, password); }
      await login(email, password);
      nav("/");
    } catch (ex) { setErr(ex?.data?.error || ex.message); }
  };

  return (
    <div className="min-h-screen grid place-items-center bg-zinc-50">
      <Card className="w-full max-w-md">
        <h1 className="text-xl font-semibold mb-2">{mode === "login" ? "Login" : "Create an account"}</h1>
        <p className="text-sm text-zinc-500 mb-4">Use your email & password.</p>
        {err && <div className="mb-3 text-red-600 text-sm">{err}</div>}
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="block text-sm mb-1">Email</label>
            <input className="w-full border border-zinc-300 rounded-xl px-3 py-2" type="email" value={email} onChange={e=>setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm mb-1">Password</label>
            <input className="w-full border border-zinc-300 rounded-xl px-3 py-2" type="password" value={password} onChange={e=>setPassword(e.target.value)} required />
          </div>
          <button className="w-full py-2 rounded-xl bg-zinc-900 text-white">{mode==="login"?"Login":"Register & Login"}</button>
        </form>
        <div className="text-sm text-zinc-500 mt-4">
          {mode === "login" ? (
            <button className="underline" onClick={()=>setMode("register")}>No account? Register</button>
          ) : (
            <button className="underline" onClick={()=>setMode("login")}>Have an account? Login</button>
          )}
        </div>
      </Card>
    </div>
  );
}