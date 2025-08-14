import React, { useEffect, useMemo, useState, useContext } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../lib/api.js";

const AuthContext = React.createContext(null);
export function useAuth(){ return useContext(AuthContext); }

export function AuthProvider({ children }){
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    try { const me = await api("/auth/me"); setUser(me); }
    catch { setUser(null); }
  };

  useEffect(() => { (async () => { await refresh(); setLoading(false); })(); }, []);

  const login = async (email, password) => {
    await api("/auth/login", { method:"POST", body:{ email, password } });
    await refresh();
  };

  // Accept optional username at register time (backend should allow it)
  const register = async (email, password, username) => {
    await api("/auth/register", { method:"POST", body:{ email, password, ...(username?{ username }: {}) } });
  };

  const setUsername = async (username) => {
    await api("/auth/username", { method:"POST", body:{ username } });
    await refresh();
  };

  const logout = async () => { await api("/auth/logout", { method:"POST" }); setUser(null); };

  const value = useMemo(() => ({ user, login, register, logout, refresh, setUsername }), [user]);
  if (loading) return <div className="w-full h-screen grid place-items-center text-zinc-400">Loading…</div>;
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function RequireAuth({ children }){
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
