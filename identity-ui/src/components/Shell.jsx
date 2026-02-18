import { NavLink, Outlet, useNavigate } from "react-router-dom";
import useSessionMonitor from "../hooks/useSessionMonitor";
import SessionExpiryModal from "./SessionExpiryModal";
import useMe from "../hooks/useMe";
import "./Shell.css";

export default function Shell() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "user";
  const { showPrompt, extendSession, logout } = useSessionMonitor();
  const { me, loadingMe } = useMe();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const accountType = me?.account_type;

  const canShow = (key) => {
    if (!accountType) return false;

    if (accountType === "person") {
      return key === "profile";
    }

    if (accountType === "requester") {
      return key === "preview" || key === "profile";
    }

    if (accountType === "admin") {
      return key !== "profile";
    }

    return false;
  };

  return (
    <div className="shell-container">
      <aside className="shell-sidebar">
        <div className="sidebar-title">Identity Admin</div>

        {showPrompt && (
          <SessionExpiryModal onExtend={extendSession} onLogout={logout} />
        )}

        <nav className="shell-nav">
          {loadingMe ? (
            <div className="nav-muted">Loading menu…</div>
          ) : (
            <>
              {canShow("preview") && (
                <NavLink to="/preview" className="nav-link">
                  Identity Preview
                </NavLink>
              )}

              {canShow("persons") && (
                <NavLink to="/persons" className="nav-link">
                  Persons
                </NavLink>
              )}

              {canShow("requesters") && (
                <NavLink to="/requesters" className="nav-link">
                  Requesters
                </NavLink>
              )}

              {canShow("policies") && (
                <NavLink to="/policies" className="nav-link">
                  Policies
                </NavLink>
              )}

              {canShow("audit") && (
                <NavLink to="/audit-logs" className="nav-link">
                  Audit Logs
                </NavLink>
              )}

              {canShow("profile") && (
                <NavLink to="/profile" className="nav-link">
                  Profile
                </NavLink>
              )}
            </>
          )}
        </nav>
      </aside>

      <div className="shell-main-wrapper">
        <header className="shell-header">
          <div className="user-info">
            Logged in as: <b>{username}</b>
            {!loadingMe && me?.account_type && (
              <span style={{ marginLeft: 8, opacity: 0.8, fontSize: 12 }}>
                ({me.account_type})
              </span>
            )}
          </div>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </header>

        <main className="shell-main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}