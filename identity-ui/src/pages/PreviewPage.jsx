import { useState } from "react";
import api from "../api/client";
import "./PreviewPage.css";

export default function PreviewPage() {
  const [personId, setPersonId] = useState("1");
  const [context, setContext] = useState("school");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function handleFetch() {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await api.get(
        `/identity/${personId}/?context=${encodeURIComponent(context)}`
      );
      setResult(res.data);
    } catch (err) {
      const data = err?.response?.data;
      setResult(data || null);
      setError("Request denied or failed. See response.");
    } finally {
      setLoading(false);
    }
  }

  const deniedReason = result?.denied_reason;
  const isDenied = Boolean(deniedReason);

  return (
    <div className="previewPage">
      <div className="previewContainer">
        <div className="previewCard">
          <h2 style={{ marginTop: 0 }}>Identity Preview</h2>

          <p className="previewSmall">
            Uses logged-in requester (JWT). Calls{" "}
            <code>/identity/&lt;id&gt;/?context=...</code>
          </p>

          <div className="previewFormGrid">
            <label>
              <div className="previewSmall">Person ID</div>
              <input
                className="previewInput"
                type="number"
                value={personId}
                onChange={(e) => setPersonId(e.target.value)}
              />
            </label>

            <label>
              <div className="previewSmall">Context</div>
              <input
                className="previewInput"
                value={context}
                onChange={(e) => setContext(e.target.value)}
              />
            </label>

            <button className="previewBtn" onClick={handleFetch} disabled={loading}>
              {loading ? "Fetching..." : "Fetch Identity"}
            </button>
          </div>

          {error && (
            <div className="previewAlert previewAlertError">
              {error}
            </div>
          )}

          {isDenied && (
            <div className="previewAlert previewAlertDenied">
              Denied: {deniedReason}
            </div>
          )}

          {result && (
            <div style={{ marginTop: 14 }}>
              <h3 style={{ margin: "10px 0" }}>API Response</h3>
              <pre className="previewPre">{JSON.stringify(result, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}