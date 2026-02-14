import { useEffect, useState } from "react";
import api from "../api/client";
import Modal from "../components/Modal";
import "./AuditLogsPage.css";

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [count, setCount] = useState(0);
  const [filters, setFilters] = useState({
    decision: "",
    context: "",
    q: "",
  });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [openDetails, setOpenDetails] = useState(false);

  function openRowDetails(row) {
    setSelected(row);
    setOpenDetails(true);
  }

  useEffect(() => {
    load();
  }, [page]);

  async function load() {
    setLoading(true);
    try {
      const res = await api.get("/api/admin/audit-logs/", {
        params: { ...filters, page },
      });
      setLogs(res.data.results);
      setCount(res.data.count);
    } catch {
      alert("Failed to load audit logs.");
    } finally {
      setLoading(false);
    }
  }

  function applyFilters() {
    setPage(1);
    load();
  }

  return (
    <div className="audit-container">
      <h2>Audit Logs</h2>

      {/* Filters */}
      <div className="audit-filters">
        <input
          placeholder="Search user or person id"
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
        />

        <input
          placeholder="Context"
          value={filters.context}
          onChange={(e) => setFilters({ ...filters, context: e.target.value })}
        />

        <select
          value={filters.decision}
          onChange={(e) =>
            setFilters({ ...filters, decision: e.target.value })
          }
        >
          <option value="">All Decisions</option>
          <option value="ALLOW">ALLOW</option>
          <option value="DENY">DENY</option>
        </select>

        <button onClick={applyFilters}>Apply</button>
      </div>

      {/* Table */}
      {loading ? (
        <div>Loading...</div>
      ) : (
        <table className="audit-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Requester</th>
              <th>Person</th>
              <th>Context</th>
              <th>Decision</th>
              <th>Fields</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}
                onClick={() => openRowDetails(log)}
                style={{ cursor: "pointer" }}>
                <td>{new Date(log.timestamp).toLocaleString()}</td>
                <td>{log.requester_username}</td>
                <td>{log.person}</td>
                <td>{log.context_used}</td>
                <td>
                  <span
                    className={
                      log.decision === "ALLOW"
                        ? "decision-allow"
                        : "decision-deny"
                    }
                  >
                    {log.decision}
                  </span>
                </td>
                <td>{(log.fields_returned || []).join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Pagination */}
      <div className="audit-pagination">
        <button disabled={page === 1} onClick={() => setPage(page - 1)}>
          Previous
        </button>
        <span>
          Page {page} — {count} total logs
        </span>
        <button onClick={() => setPage(page + 1)}>Next</button>
      </div>
      <Modal
        open={openDetails}
        title={selected ? `Audit Log #${selected.id}` : "Audit Log"}
        onClose={() => setOpenDetails(false)}
      >
        {!selected ? null : (
          <div className="detailsGrid">
            <div className="detailsKey">Timestamp</div>
            <div className="detailsVal">{selected.timestamp || selected.time}</div>

            <div className="detailsKey">Decision</div>
            <div className="detailsVal">
              <span className={selected.decision === "ALLOW" ? "badgeAllow" : "badgeDeny"}>
                {selected.decision}
              </span>
            </div>

            <div className="detailsKey">Requester</div>
            <div className="detailsVal">
              {selected.requester_username ? (
                <>
                  {selected.requester_username}{" "}
                  <span className="mono" style={{ opacity: 0.7 }}>
                    (id: {selected.requester_id ?? selected.requester})
                  </span>
                </>
              ) : (
                <span className="mono">{selected.requester_id ?? selected.requester}</span>
              )}
            </div>

            <div className="detailsKey">Requester role</div>
            <div className="detailsVal">{selected.requester_role || "-"}</div>

            <div className="detailsKey">Person</div>
            <div className="detailsVal">
              <span className="mono">{selected.person_id ?? selected.person}</span>
            </div>

            <div className="detailsKey">Context</div>
            <div className="detailsVal">{selected.context_used || selected.context}</div>

            <div className="detailsKey">Fields returned</div>
            <div className="detailsVal">
              {(selected.fields_returned || selected.fields || []).length
                ? (selected.fields_returned || selected.fields).join(", ")
                : "—"}
            </div>

            <div className="detailsKey">Denied reason</div>
            <div className="detailsVal">{selected.denied_reason || "—"}</div>

            <div className="detailsKey">Signature</div>
            <div className="detailsVal mono">{selected.signature || "—"}</div>

            <div className="detailsKey">Prev signature</div>
            <div className="detailsVal mono">{selected.prev_signature || "—"}</div>
          </div>
        )}
      </Modal>
    </div>
  );
}