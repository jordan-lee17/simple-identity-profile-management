import { useEffect, useMemo, useState } from "react";
import api from "../api/client";
import "./PoliciesPage.css";

const NAME_TYPES = ["legal", "preferred", "professional"];

function formatErrors(errObj) {
  if (!errObj) return "Save failed.";
  if (typeof errObj === "string") return errObj;

  try {
    return Object.entries(errObj)
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(" ") : String(v)}`)
      .join("\n");
  } catch {
    return JSON.stringify(errObj, null, 2);
  }
}

export default function PoliciesPage() {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");
  const [err, setErr] = useState("");

  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    context_name: "",
    required_role: "",
    allowed_name_types: [],
    additional_rules: { allow_high: false },
  });

  const [toast, setToast] = useState(null);
  const [flashId, setFlashId] = useState(null);

  function showToast(title, body, variant = "ok") {
    setToast({ title, body, variant });
    window.clearTimeout(showToast._t);
    showToast._t = window.setTimeout(() => setToast(null), 2500);
  }

  async function load() {
    setLoading(true);
    setErr("");
    try {
      const res = await api.get("/api/admin/policies/");
      setPolicies(res.data);
    } catch {
      setErr("Failed to load policies. Make sure you are logged in as an admin requester.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return policies;
    return policies.filter(
      (p) =>
        p.context_name?.toLowerCase().includes(q) ||
        p.required_role?.toLowerCase().includes(q)
    );
  }, [policies, query]);

  function startNew() {
    setEditing(null);
    setErr("");
    setForm({
      context_name: "",
      required_role: "",
      allowed_name_types: [],
      additional_rules: { allow_high: false },
    });
  }

  function startEdit(p) {
    setEditing(p);
    setErr("");
    setForm({
      context_name: p.context_name,
      required_role: p.required_role,
      allowed_name_types: p.allowed_name_types || [],
      additional_rules: p.additional_rules || { allow_high: false },
    });
  }

  function toggleType(t) {
    setForm((prev) => {
      const exists = prev.allowed_name_types.includes(t);
      return {
        ...prev,
        allowed_name_types: exists
          ? prev.allowed_name_types.filter((x) => x !== t)
          : [...prev.allowed_name_types, t],
      };
    });
  }

  async function save() {
    setErr("");
    try {
      let saved;

      if (editing) {
        const res = await api.put(`/api/admin/policies/${editing.id}/`, form);
        saved = res.data;
        showToast("Saved", `Updated policy "${saved.context_name}".`, "ok");
      } else {
        const res = await api.post("/api/admin/policies/", form);
        saved = res.data;
        showToast("Created", `Created policy "${saved.context_name}".`, "ok");
      }

      // Refresh so list is always accurate
      await load();

      // Reopen editor on the saved item + flash row
      setEditing(saved);
      setForm({
        context_name: saved.context_name,
        required_role: saved.required_role,
        allowed_name_types: saved.allowed_name_types || [],
        additional_rules: saved.additional_rules || { allow_high: false },
      });

      setFlashId(saved.id);
      window.setTimeout(() => setFlashId(null), 1300);
    } catch (e) {
      setErr(formatErrors(e?.response?.data));
      showToast("Action failed", "Please check the form fields and try again.", "warn");
    }
  }


  async function remove(p) {
    if (!window.confirm(`Delete policy "${p.context_name}"?`)) return;
    setErr("");
    try {
      await api.delete(`/api/admin/policies/${p.id}/`);
      setPolicies((prev) => prev.filter((x) => x.id !== p.id));
      if (editing?.id === p.id) startNew();
    } catch {
      setErr("Delete failed.");
    }
  }

  return (
    <div className="policiesWrap">
      <div className="policiesCard">
        <div className="policiesTop">
          <div>
            <h1 className="policiesTitle">Policies</h1>
            <div className="policiesSub">
              Manage ABAC disclosure rules. Endpoint: <code>/api/admin/policies/</code>
            </div>
          </div>
          <button className="btn" onClick={load} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>

        {err && <div className="errorBox">{err}</div>}

        <div className="policiesGrid">
          {/* LEFT: LIST */}
          <div className="panel">
            <div className="panelHeader">
              <div>
                <div style={{ fontWeight: 700 }}>Policy list</div>
                <div className="small">Click a row to edit</div>
              </div>
            </div>

            <div className="searchRow">
              <input
                className="input"
                placeholder="Search by context or role (e.g. school, doctor)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button className="btn btnGhost" onClick={() => setQuery("")} disabled={!query}>
                Clear
              </button>
            </div>

            <table className="table">
              <thead>
                <tr>
                  <th className="th">Context</th>
                  <th className="th">Required role</th>
                  <th className="th">Allowed name types</th>
                  <th className="th" />
                </tr>
              </thead>
              <tbody>
                {filtered.map((p) => {
                  const selected = editing?.id === p.id;
                  return (
                    <tr
                      key={p.id}
                      className={`tr ${flashId === p.id ? "rowFlash" : ""}`}
                      style={selected ? { background: "rgba(27,42,82,0.25)" } : {}}
                    >
                      <td className="td">
                        <button className="rowBtn" onClick={() => startEdit(p)}>
                          <span style={{ fontWeight: 700 }}>{p.context_name}</span>
                        </button>
                      </td>
                      <td className="td">
                        <span className="badge">{p.required_role}</span>
                      </td>
                      <td className="td">
                        <div className="typeList">
                          {(p.allowed_name_types || []).map((t) => (
                            <span key={t} className="badge">
                              {t}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="td" style={{ textAlign: "right" }}>
                        <button className="btn btnDanger" onClick={() => remove(p)}>
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })}

                {!loading && filtered.length === 0 && (
                  <tr className="tr">
                    <td className="td small" colSpan={4}>
                      No matches. Try another search or create a new policy.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          {/* RIGHT: EDITOR */}
          <div className="panel sticky">
            <div className="panelHeader">
              <div>
                <div style={{ fontWeight: 800, fontSize: 18 }}>
                  {editing ? `Edit: ${editing.context_name}` : "Create new policy"}
                </div>
                <div className="small">
                  {editing ? "Update fields and save." : "Fill in details then create."}
                </div>
              </div>

              <button className="btn" onClick={startNew}>
                New
              </button>
            </div>

            <div className="formGrid">
              <label>
                <div className="small">Context name</div>
                <input
                  className="input"
                  value={form.context_name}
                  onChange={(e) => setForm({ ...form, context_name: e.target.value })}
                  disabled={!!editing}
                  placeholder="e.g. school, job, healthcare"
                />
                {editing && (
                  <div className="small">Locked during edit (context name is unique).</div>
                )}
              </label>

              <label>
                <div className="small">Required requester role</div>
                <input
                  className="input"
                  value={form.required_role}
                  onChange={(e) => setForm({ ...form, required_role: e.target.value })}
                  placeholder="e.g. teacher, employer, doctor"
                />
              </label>

              <div>
                <div className="small">Allowed name types</div>
                <div className="checkRow">
                  {NAME_TYPES.map((t) => (
                    <label key={t} className="small">
                      <input
                        type="checkbox"
                        checked={form.allowed_name_types.includes(t)}
                        onChange={() => toggleType(t)}
                      />{" "}
                      {t}
                    </label>
                  ))}
                </div>
              </div>

              <label className="small">
                <input
                  type="checkbox"
                  checked={!!form.additional_rules?.allow_high}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      additional_rules: {
                        ...(form.additional_rules || {}),
                        allow_high: e.target.checked,
                      },
                    })
                  }
                />{" "}
                Allow high-sensitivity names (override)
              </label>

              <button className="btn" onClick={save}>
                {editing ? "Save changes" : "Create policy"}
              </button>

              {editing && (
                <button className="btn btnGhost" onClick={startNew}>
                  Cancel editing
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
      {toast && (
        <div className={`toast ${toast.variant === "ok" ? "toastOk" : "toastWarn"}`}>
          <div className="toastTitle">{toast.title}</div>
          <div className="toastBody">{toast.body}</div>
        </div>
      )}
    </div>
  );
}