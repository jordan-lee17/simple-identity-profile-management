import { Navigate } from "react-router-dom";
import useMe from "../hooks/useMe";

export default function RequireAccountType({ allowedTypes, children }) {
  const { me, loadingMe } = useMe();

  if (loadingMe) return <div style={{ padding: 16 }}>Loading…</div>;

  if (!me?.account_type) return <Navigate to="/login" replace />;

  if (!allowedTypes.includes(me.account_type)) {
    // If user tries to visit a page they can't access, send them to their home
    const home =
      me.account_type === "person"
        ? "/profile"
        : me.account_type === "requester"
        ? "/preview"
        : "/preview";
    return <Navigate to={home} replace />;
  }

  return children;
}