import { useState } from 'react'
import './App.css'

function App() {
  const [personId, setPersonId] = useState("1");
  const [role, setRole] = useState("teacher");
  const [context, setContext] = useState("school");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleFetch = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const url = `http://127.0.0.1:8000/identity/${personId}/?role=${encodeURIComponent(
        role
      )}&context=${encodeURIComponent(context)}`;

      const res = await fetch(url);

      if (!res.ok) {
        throw new Error(`Request failed: ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        fontFamily: "system-ui, sans-serif",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "#f4f4f5",
      }}
    >
      <div
        style={{
          background: "white",
          padding: "2rem",
          borderRadius: "1rem",
          boxShadow: "0 10px 25px rgba(0,0,0,0.08)",
          width: "420px",
        }}
      >
        <h1 style={{ fontSize: "1.5rem", marginBottom: "1rem" }}>
          Identity Preview (Prototype)
        </h1>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <label>
            Person ID
            <input
              type="number"
              value={personId}
              onChange={(e) => setPersonId(e.target.value)}
              style={{ width: "100%", padding: "0.4rem", marginTop: "0.25rem" }}
            />
          </label>

          <label>
            Requester Role
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              style={{ width: "100%", padding: "0.4rem", marginTop: "0.25rem" }}
            >
              <option value="teacher">Teacher</option>
              <option value="employer">Employer</option>
              <option value="anonymous">Anonymous</option>
            </select>
          </label>

          <label>
            Context
            <input
              type="text"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="e.g. school, job, healthcare"
              style={{ width: "100%", padding: "0.4rem", marginTop: "0.25rem" }}
            />
          </label>

          <button
            onClick={handleFetch}
            disabled={loading}
            style={{
              marginTop: "0.5rem",
              padding: "0.6rem",
              borderRadius: "0.5rem",
              border: "none",
              background: "#2563eb",
              color: "white",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            {loading ? "Fetching..." : "Fetch Identity"}
          </button>
        </div>

        {error && (
          <div
            style={{
              marginTop: "1rem",
              padding: "0.5rem",
              borderRadius: "0.5rem",
              background: "#fee2e2",
              color: "#991b1b",
              fontSize: "0.9rem",
            }}
          >
            Error: {error}
          </div>
        )}

        {result && (
          <div style={{ marginTop: "1rem" }}>
            <h2 style={{ fontSize: "1rem", marginBottom: "0.3rem" }}>
              API Response
            </h2>
            <pre
              style={{
                background: "#0f172a",
                color: "#e5e7eb",
                padding: "0.75rem",
                borderRadius: "0.5rem",
                fontSize: "0.8rem",
                maxHeight: "220px",
                overflow: "auto",
              }}
            >
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;