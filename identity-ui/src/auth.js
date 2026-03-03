import api from "./api/client";

export function isLoggedIn() {
  return Boolean(localStorage.getItem("access"));
}

export async function login(username, password) {
  const res = await api.post("/api/token/", { username, password });
  localStorage.setItem("access", res.data.access);
  localStorage.setItem("refresh", res.data.refresh);
  localStorage.setItem("username", username);
  return res.data;
}

export async function logout() {
  const refresh = localStorage.getItem("refresh");
  try {
    if (refresh) await api.post("/api/logout/", { refresh });
  } catch {
    // Ignore errors
  } finally {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    localStorage.removeItem("username");
  }
}

export async function refreshToken() {
  const refresh = localStorage.getItem("refresh");
  if (!refresh) throw new Error("No refresh token available");

  try {
    const res = await api.post("/api/token/refresh/", { refresh });
    localStorage.setItem("access", res.data.access);
    return res.data.access;
  } catch (error) {
    logout();
    throw error;
  }
}