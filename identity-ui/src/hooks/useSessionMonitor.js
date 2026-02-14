import { useEffect, useState } from "react";
import { jwtDecode } from "jwt-decode";
import { refreshToken, logout } from "../auth";

export default function useSessionMonitor() {
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      const token = localStorage.getItem("access");
      if (!token) return;

      const decoded = jwtDecode(token);
      const now = Date.now() / 1000;

      // If less than 120s left
      if (decoded.exp - now < 120) {
        setShowPrompt(true);
      }
      // Check every 30s
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  async function extendSession() {
    try {
      await refreshToken();
      setShowPrompt(false);
    } catch {
      logout();
    }
  }

  return { showPrompt, extendSession, logout };
}