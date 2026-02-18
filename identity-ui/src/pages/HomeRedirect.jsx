import { Navigate } from "react-router-dom";
import useMe from "../hooks/useMe";

export default function HomeRedirect() {
    const { me, loadingMe } = useMe();

    if (loadingMe) return <div style={{ padding: 16 }}>Loading…</div>;
    if (!me?.account_type) return <Navigate to="/login" replace />;
    if (me.account_type === "person") {
        return <Navigate to="/profile" replace />;
    }
    if (me.account_type === "requester") return <Navigate to="/preview" replace />;
    return <Navigate to="/preview" replace />;
}