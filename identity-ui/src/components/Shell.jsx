import { NavLink, Outlet, useNavigate } from "react-router-dom";
import useSessionMonitor from "../hooks/useSessionMonitor";
import SessionExpiryModal from "./SessionExpiryModal";
import "./Shell.css";

export default function Shell() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "user";
  const { showPrompt, extendSession, logout } = useSessionMonitor()

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="shell-container">
      <aside className="shell-sidebar">
        <div className="sidebar-title">Identity Admin</div>
        {showPrompt && (
          <SessionExpiryModal
            onExtend={extendSession}
            onLogout={logout}
          />
        )}

        <nav className="shell-nav">
          <NavLink to="/preview" className="nav-link">
            Identity Preview
          </NavLink>
          <NavLink to="/persons" className="nav-link">
            Persons
          </NavLink>
          <NavLink to="/requesters" className="nav-link">
            Requesters
          </NavLink>
          <NavLink to="/policies" className="nav-link">
            Policies
          </NavLink>
          <NavLink to="/audit-logs" className="nav-link">
            Audit Logs
          </NavLink>
          <NavLink to="/profile" className="nav-link">
            Profile
          </NavLink>
        </nav>
      </aside>

      <div className="shell-main-wrapper">
        <header className="shell-header">
          <div className="user-info">
            Logged in as: <b>{username}</b>
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