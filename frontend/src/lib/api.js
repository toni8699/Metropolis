const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8080";

function authHeaders() {
  const token = localStorage.getItem("accessToken");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiGet(path, withAuth = false) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(withAuth ? authHeaders() : {}),
    },
  });
  return response.json();
}

export async function apiPost(path, body, withAuth = false) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(withAuth ? authHeaders() : {}),
    },
    body: JSON.stringify(body),
  });
  return response.json();
}

export async function apiPatch(path, body, withAuth = false) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...(withAuth ? authHeaders() : {}),
    },
    body: JSON.stringify(body),
  });
  return response.json();
}

export function setAccessToken(token) {
  localStorage.setItem("accessToken", token);
}
