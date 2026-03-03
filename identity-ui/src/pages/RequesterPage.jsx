import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";

export default function PersonsPage() {
  const nav = useNavigate();

  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [data, setData] = useState({ count: 0, results: [] });

  const [showCreate, setShowCreate] = useState(false);

  const [createForm, setCreateForm] = useState({
    username: "",
    password: "",
    email: "",
    organisation_name: "",
    role: "",
  });

  const [createSaving, setCreateSaving] = useState(false);
  const [createErr, setCreateErr] = useState("");
  const [toast, setToast] = useState(null);

  function showToast(title, body, variant = "ok") {
    setToast({ title, body, variant });
    window.clearTimeout(showToast._t);
    showToast._t = window.setTimeout(() => setToast(null), 2500);
  }

  function openCreateModal() {
    setCreateErr("");
    setCreateSaving(false);
    setCreateForm({
      username: "",
      password: "",
      email: "",
      organisation_name: "",
      role: "",
    });
    setShowCreate(true);
  }

  function closeCreateModal() {
    setShowCreate(false);
    setCreateErr("");
  }

  function onCreateChange(e) {
    const { name, value } = e.target;
    setCreateForm((p) => ({ ...p, [name]: value }));
  }

  async function onCreateSubmit(e) {
    e.preventDefault();
    setCreateErr("");
    setCreateSaving(true);

    try {
      const res = await api.post("/api/admin/requesters/", createForm);

      showToast("Created", `Requester created (id: ${res.data.requester_id}).`, "ok");

      await load();

      setShowCreate(false);
    } catch (e2) {
      const data = e2?.response?.data;
      const msg = data?.detail || JSON.stringify(data) || "Create failed.";
      setCreateErr(msg);
      showToast("Failed", "Please check the form and try again.", "warn");
    } finally {
      setCreateSaving(false);
    }
  }

  async function load() {
    setLoading(true);
    setErr("");
    try {
      const res = await api.get("/api/admin/requesters/", {
        params: { q, page, page_size: pageSize },
      });
      setData(res.data);
    } catch (e) {
      setErr("Failed to load requesters. Are you logged in as an admin requester?");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [page]);

  function onSearchSubmit(e) {
    e.preventDefault();
    setPage(1);
    load();
  }

  const totalPages = Math.max(1, Math.ceil((data.count || 0) / pageSize));

  return (
    <div className="persons-card">
      <div className="persons-header">
        <div>
          <h2 className="persons-title">Requesters</h2>
          <div className="persons-subtitle">
            Admin-only listing via <code>/api/admin/requesters/</code>
          </div>
          <button className="persons-btn persons-actions" type="button" onClick={openCreateModal}>
            Create requester
          </button>
        </div>

        <form className="persons-search" onSubmit={onSearchSubmit}>
          <input
            className="persons-searchInput"
            placeholder="Search username / organisation / role"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button className="persons-btn" type="submit">
            Search
          </button>
          <button className="persons-btn persons-btnSecondary" type="button" onClick={() => { setQ(""); setPage(1); }}>
            Clear
          </button>
        </form>
      </div>

      {loading && <div className="persons-muted">Loading…</div>}
      {err && <div className="persons-error">{err}</div>}

      {!loading && !err && (
        <>
          <div className="persons-tableWrap">
            <table className="persons-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Organisation</th>
                  <th>Role</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.results.map((p) => (
                  <tr key={p.id}>
                    <td className="persons-mono">{p.id}</td>
                    <td className="persons-mono">{p.username}</td>
                    <td className="persons-mono">{p.email}</td>
                    <td className="persons-mono">{p.organisation_name}</td>
                    <td className="persons-mono">{p.role}</td>
                  </tr>
                ))}

                {data.results.length === 0 && (
                  <tr>
                    <td colSpan="4" className="persons-muted" style={{ padding: 16 }}>
                      No persons found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="persons-footer">
            <div className="persons-muted">
              Showing page {page} / {totalPages} — {data.count} total
            </div>

            <div className="persons-pager">
              <button
                className="persons-btn persons-btnSecondary"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Prev
              </button>
              <button
                className="persons-btn persons-btnSecondary"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
              <button className="persons-btn" onClick={load}>
                Refresh
              </button>
            </div>
          </div>
        </>
      )}

      {showCreate && (
        <div
          className="modalOverlay"
          onMouseDown={(e) => {
            // close if click outside modal card
            if (e.target === e.currentTarget) closeCreateModal();
          }}
        >
          <div className="modalCard">
            <div className="modalHeader">
              <div>
                <h3 className="modalTitle">Create Requester Account</h3>
                <div className="modalSubtitle">
                  POST <code>/api/admin/requesters/</code>
                </div>
              </div>
              <button className="persons-btn persons-btnSecondary" type="button" onClick={closeCreateModal}>
                Close
              </button>
            </div>

            {createErr && <div className="modalErr">{createErr}</div>}

            <form onSubmit={onCreateSubmit} className="modalForm">
              <label className="modalField">
                <div className="modalLabel">Username</div>
                <input
                  className="modalInput"
                  name="username"
                  value={createForm.username}
                  onChange={onCreateChange}
                  required
                />
              </label>

              <label className="modalField">
                <div className="modalLabel">Password</div>
                <input
                  className="modalInput"
                  name="password"
                  type="password"
                  value={createForm.password}
                  onChange={onCreateChange}
                  required
                />
              </label>

              <label className="modalField">
                <div className="modalLabel">Email</div>
                <input
                  className="modalInput"
                  name="email"
                  value={createForm.email}
                  onChange={onCreateChange}
                  required
                />
              </label>

              <label className="modalField">
                <div className="modalLabel">Organisation name</div>
                <input
                  className="modalInput"
                  name="organisation_name"
                  value={createForm.organisation_name}
                  onChange={onCreateChange}
                  required
                />
              </label>

              <label className="modalField">
                <div className="modalLabel">Role</div>
                <input
                  className="modalInput"
                  name="role"
                  value={createForm.role}
                  onChange={onCreateChange}
                  required
                />
              </label>

              <div className="modalActions">
                <button className="persons-btn" disabled={createSaving}>
                  {createSaving ? "Creating..." : "Create"}
                </button>
                <button
                  className="persons-btn persons-btnSecondary"
                  type="button"
                  onClick={closeCreateModal}
                  disabled={createSaving}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}