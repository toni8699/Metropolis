const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

function buildHeaders(includeAuth, extraHeaders = {}) {
  const headers = { "Content-Type": "application/json", ...extraHeaders };
  if (includeAuth) {
    const token = localStorage.getItem("accessToken");
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }
  return headers;
}

export async function apiRequest(path, options = {}) {
  const { withAuth = false, headers, ...rest } = options;
  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: buildHeaders(withAuth, headers),
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const message =
      payload?.message ||
      payload?.error?.message ||
      payload?.error ||
      "Request failed";
    throw new Error(message);
  }

  return payload;
}

export function apiGet(path, withAuth = false) {
  return apiRequest(path, { method: "GET", withAuth });
}

export function apiPost(path, body, withAuth = false) {
  return apiRequest(path, {
    method: "POST",
    body: JSON.stringify(body),
    withAuth,
  });
}

export function apiPatch(path, body, withAuth = false) {
  return apiRequest(path, {
    method: "PATCH",
    body: JSON.stringify(body),
    withAuth,
  });
}
