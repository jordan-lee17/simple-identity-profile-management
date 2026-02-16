import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import "./PersonsPage.css";

export default function PersonsPage() {
  const nav = useNavigate();

  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [data, setData] = useState({ count: 0, results: [] });

  async function load() {
    setLoading(true);
    setErr("");
    try {
      const res = await api.get("/api/admin/persons/", {
        params: { q, page, page_size: pageSize },
      });
      setData(res.data);
    } catch (e) {
      setErr("Failed to load persons. Are you logged in as an admin requester?");
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
          <h2 className="persons-title">Persons</h2>
          <div className="persons-subtitle">
            Admin-only listing via <code>/api/admin/persons/</code>
          </div>
        </div>

        <form className="persons-search" onSubmit={onSearchSubmit}>
          <input
            className="persons-searchInput"
            placeholder="Search name / public_id…"
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
                  <th>Label</th>
                  <th>Created At</th>
                  <th>Updated At</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.results.map((p) => (
                  <tr key={p.id}>
                    <td className="persons-mono">{p.id}</td>
                    <td className="persons-mono">{p.label}</td>
                    <td className="persons-mono">{p.created_at ? new Date(p.created_at).toLocaleString() : "-"}</td>
                    <td className="persons-mono">{p.updated_at ? new Date(p.updated_at).toLocaleString() : "-"}</td>
                    <td className="persons-actions">
                      <button
                        className="persons-btn"
                        onClick={() => nav(`/preview?personId=${p.id}`)}
                      >
                        Preview
                      </button>
                      <button
                        className="persons-btn persons-btnSecondary"
                        onClick={() => nav(`/persons/${p.id}`)}
                      >
                        Edit
                      </button>
                    </td>
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
    </div>
  );
}