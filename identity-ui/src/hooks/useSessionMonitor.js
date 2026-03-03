import { useEffect, useState } from "react";
import { jwtDecode } from "jwt-decode";
import { refreshToken, logout } from "../auth";

export default function useSessionMonitor() {
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access");
    if (!token) return;

    let warnTimer;
    let logoutTimer;

    try {
      const { exp } = jwtDecode(token);
      const now = Date.now() / 1000;
      const timeLeft = exp - now;

      if (timeLeft <= 0) {
        setShowPrompt(false);
        logout();
        return;
      }

      // Warn 2 minutes before expiry
      const warnMs = Math.max((timeLeft - 120) * 1000, 0);
      warnTimer = setTimeout(() => setShowPrompt(true), warnMs);

      // Auto logout on expiry
      logoutTimer = setTimeout(() => logout(), timeLeft * 1000);
    } catch {
      logout();
    }

    return () => {
      clearTimeout(warnTimer);
      clearTimeout(logoutTimer);
    };
  }, []);

  async function extendSession() {
    try {
      await refreshToken();
      setShowPrompt(false);
    } catch {
      setShowPrompt(false);
      logout();
    }
  }

  return { showPrompt, extendSession, logout };
}