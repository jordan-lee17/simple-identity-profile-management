import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, isLoggedIn } from "../auth";
import "./LoginPage.css";

export default function LoginPage() {
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  React.useEffect(() => {
    if (isLoggedIn()) nav("/preview");
  }, [nav]);

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    try {
      await login(username, password);
      nav("/preview");
    } catch {
      setErr("Login failed. Check username/password.");
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h2 className="login-title">Admin Login</h2>
        <p className="login-subtitle">
          Uses JWT: <code>/api/token/</code>
        </p>

        <form onSubmit={onSubmit} className="login-form">
          <input
            className="login-input"
            placeholder="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            className="login-input"
            type="password"
            placeholder="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="login-btn" type="submit">
            Login
          </button>
          <button
            type="button"
            className="login-btn login-btn-secondary"
            onClick={() => nav("/register")}
          >
            Register
          </button>
          {err && <div className="login-error">{err}</div>}
        </form>
      </div>
    </div>
  );
}