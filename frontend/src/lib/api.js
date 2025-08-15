// api.js
const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, ""); // no trailing slash

function join(base, p) {
  if (!base) return p;                                 // allow same-origin if you ever serve UI + API together
  return `${base}/${String(p).replace(/^\/+/, "")}`;   // ensure exactly one slash
}

export const apiGet = (p, opts) => api(p, { ...opts, method: "GET" });

export async function api(path, { method = "GET", body, headers = {} } = {}) {
  const url = join(API_BASE, path);
  try {
    const res = await fetch(url, {
      method,
      headers: {
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
      credentials: "include", // needed for Flask-Login cookies
    });

    const ct = res.headers.get("content-type") || "";
    const data = ct.includes("application/json") ? await res.json() : await res.text();

    if (!res.ok) {
      throw Object.assign(new Error(data?.error || res.statusText), { status: res.status, data, url });
    }
    return data;
  } catch (err) {
    // Network/CORS errors land here; surface the URL for debugging
    err.url = url;
    throw err;
  }
}