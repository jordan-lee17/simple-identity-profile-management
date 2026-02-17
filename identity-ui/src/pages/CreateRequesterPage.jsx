import { useState } from "react";
import api from "../api/client";
import Toast from "../components/Toast";
import "./CreateRequesterPage.css";

export default function CreateRequesterPage() {
  const [form, setForm] = useState({
    username: "",
    password: "",
    email: "",
    organisation_name: "",
    role: "",
  });

  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");
  const [toast, setToast] = useState(null);

  function showToast(title, body, variant = "ok") {
    setToast({ title, body, variant });
    window.clearTimeout(showToast._t);
    showToast._t = window.setTimeout(() => setToast(null), 2500);
  }

  function onChange(e) {
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }));
  }

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    setSaving(true);

    try {
      const res = await api.post("/api/admin/requesters/", form);
      showToast("Created", `Requester created (id: ${res.data.requester_id}).`, "ok");

      setForm({
        username: "",
        password: "",
        email: "",
        organisation_name: "",
        role: "",
      });
    } catch (e2) {
      const data = e2?.response?.data;
      const msg = data?.detail || JSON.stringify(data) || "Create failed.";
      setErr(msg);
      showToast("Failed", "Please check the form and try again.", "warn");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="cr-wrap">
      <div className="cr-card">
        <div className="cr-head">
          <h2>Create Requester Account</h2>
          <div className="cr-sub">POST <code>/api/admin/requesters/</code></div>
        </div>

        {err && <div className="cr-err">{err}</div>}

        <form onSubmit={onSubmit} className="cr-form">
          <label>
            Username
            <input name="username" value={form.username} onChange={onChange} required />
          </label>

          <label>
            Password
            <input name="password" type="password" value={form.password} onChange={onChange} required />
          </label>

          <label>
            Email
            <input name="email" value={form.email} onChange={onChange} required />
          </label>

          <label>
            Organisation name
            <input name="organisation_name" value={form.organisation_name} onChange={onChange} required />
          </label>

          <label>
            Role
            <input name="role" value={form.role} onChange={onChange} required />
          </label>

          <button className="btn primary" disabled={saving}>
            {saving ? "Creating..." : "Create requester"}
          </button>
        </form>
      </div>

      <Toast toast={toast} />
    </div>
  );
}