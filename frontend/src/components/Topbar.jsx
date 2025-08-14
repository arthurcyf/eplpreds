import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Topbar(){
  const { user, logout } = useAuth();
  const nav = useNavigate();
  return (
    <div className="w-full border-b border-zinc-200 bg-white/70 backdrop-blur sticky top-0 z-40">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="font-semibold tracking-tight">EPL Predictor</Link>
        <div className="flex items-center gap-3 text-sm">
          {user && <span className="text-zinc-500">User #{user.id}</span>}
          {user ? (
            <button onClick={async()=>{await logout(); nav("/login");}}
              className="px-3 py-1.5 rounded-xl bg-zinc-900 text-white hover:bg-zinc-800">Logout</button>
          ) : (
            <Link to="/login" className="px-3 py-1.5 rounded-xl bg-zinc-900 text-white">Login</Link>
          )}
        </div>
      </div>
    </div>
  );
}