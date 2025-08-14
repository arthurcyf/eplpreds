export const BASE_URL = ""; // e.g. "http://localhost:3000" if different origin

export async function api(path, { method = "GET", body, headers = {} } = {}) {
  const res = await fetch(`${BASE_URL}${path}`.replace(/\/+$/, ""), {
    method,
    headers: { "Content-Type": "application/json", ...headers },
    credentials: "include",
    body: body ? JSON.stringify(body) : undefined,
  });
  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) {
    throw Object.assign(new Error(data?.error || res.statusText), { status: res.status, data });
  }
  return data;
}