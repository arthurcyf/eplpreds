// api.js
const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");
const join = (b, p) => (b ? `${b}/${String(p).replace(/^\/+/, "")}` : p);

export const apiGet = (p, opts) => api(p, { ...opts, method: "GET" });

export async function api(path, { method = "GET", body, headers = {} } = {}) {
  const url = join(API_BASE, path);

  // If it's FormData, don't set Content-Type; let the browser set boundary.
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  const payload = isFormData
    ? body
    : body != null
    ? JSON.stringify(body)
    : undefined;

  const res = await fetch(url, {
    method,
    credentials: "include",
    headers: {
      ...(!isFormData && body != null ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: payload,               // <- this was missing
  });

  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) throw Object.assign(new Error(data?.error || res.statusText), { status: res.status, data, url });
  return data;
}