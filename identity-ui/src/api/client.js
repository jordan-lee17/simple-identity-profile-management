import axios from "axios";
import { refreshToken, logout } from "../auth";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// Attach access token on every request
api.interceptors.request.use((config) => {
  const access = localStorage.getItem("access");
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

let isRefreshing = false;
let queue = [];

function resolveQueue(error, token = null) {
  queue.forEach((p) => (error ? p.reject(error) : p.resolve(token)));
  queue = [];
}

// Auto refresh on 401 and retry original request
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;

    if (!err.response) return Promise.reject(err);

    if (err.response.status === 401 && !original._retry) {
      original._retry = true;

      // If no refresh token
      const refresh = localStorage.getItem("refresh");
      if (!refresh) {
        logout();
        window.location.href = "/login";
        return Promise.reject(err);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          queue.push({ resolve, reject });
        }).then((newAccess) => {
          original.headers.Authorization = `Bearer ${newAccess}`;
          return api(original);
        });
      }

      isRefreshing = true;

      try {
        const newAccess = await refreshToken();
        resolveQueue(null, newAccess);
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      } catch (e) {
        resolveQueue(e, null);
        logout();
        window.location.href = "/login";
        return Promise.reject(e);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(err);
  }
);

export default api;