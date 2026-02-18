import { useEffect, useState } from "react";
import api from "../api/client";

export default function useMe() {
  const [me, setMe] = useState(null);
  const [loadingMe, setLoadingMe] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function load() {
      setLoadingMe(true);
      try {
        const res = await api.get("/api/me/");
        if (mounted) setMe(res.data);
      } catch {
        if (mounted) setMe(null);
      } finally {
        if (mounted) setLoadingMe(false);
      }
    }

    load();
    return () => { mounted = false; };
  }, []);

  return { me, loadingMe };
}