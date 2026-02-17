import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/client";
import "./AdminEditPersonPage.css";
import Toast from "../components/Toast";

const TYPES = ["legal", "preferred", "professional"];
const SENS = ["low", "medium", "high"];

function normalizeRecords(nameRecords) {
    // Convert list to map for easy form editing
    const map = {};
    for (const t of TYPES) map[t] = { value: "", sensitivity_level: "low", exists: false };

    for (const r of nameRecords || []) {
        const t = (r.type || "").toLowerCase();
        if (map[t]) {
            map[t] = {
                value: r.value || "",
                sensitivity_level: r.sensitivity_level || "low",
                exists: true,
            };
        }
    }
    return map;
}

export default function AdminPersonEditPage() {
    const { personId } = useParams();
    const nav = useNavigate();

    const [loading, setLoading] = useState(true);
    const [savingType, setSavingType] = useState(null);
    const [err, setErr] = useState("");
    const [toast, setToast] = useState(null);

    const [records, setRecords] = useState(() => normalizeRecords([]));

    function showToast(title, body, variant = "ok") {
        setToast({ title, body, variant });
        window.clearTimeout(showToast._t);
        showToast._t = window.setTimeout(() => setToast(null), 2500);
    }

    async function load() {
        setLoading(true);
        setErr("");
        try {
            const res = await api.get(`/api/admin/persons/${personId}/names/`);
            setRecords(normalizeRecords(res.data?.name_records));
        } catch (e) {
            setErr("Failed to load profile. Are you logged in as admin?");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        load();
    }, [personId]);

    function setField(type, field, value) {
        setRecords((prev) => ({
            ...prev,
            [type]: { ...prev[type], [field]: value },
        }));
    }

    async function saveType(type) {
        setErr("");
        setSavingType(type);

        try {
            const payload = {
                type,
                value: records[type].value,
                sensitivity_level: records[type].sensitivity_level,
            };

            await api.put(`/api/admin/persons/${personId}/names/`, payload);

            showToast("Saved", `${type.toUpperCase()} name updated successfully.`, "ok");
            await load();
        } catch (e) {
            const msg = e?.response?.data
                ? JSON.stringify(e.response.data)
                : "Save failed.";
            setErr(msg);
            showToast("Update failed", "Please check the fields and try again.", "warn");
        } finally {
            setSavingType(null);
        }
    }

    return (
        <div className="admin-edit">
            <div className="admin-edit__header">
                <div>
                    <h2 className="admin-edit__title">Edit Person Profile</h2>
                    <div className="admin-edit__subtitle">Person ID: {personId}</div>
                </div>

                <button className="btn btn--ghost" onClick={() => nav(-1)}>
                    Back
                </button>
            </div>

            {loading && <div className="muted">Loading...</div>}
            {err && <div className="alert alert--error">{err}</div>}

            {!loading && (
                <div className="cards">
                    {TYPES.map((t) => (
                        <div key={t} className="card">
                            <div className="card__head">
                                <div>
                                    <div className="card__title">{t.toUpperCase()} Name</div>
                                    <div className="muted">
                                        {t === "legal"
                                            ? "Admin-controlled. Used in strict contexts."
                                            : "Admin may override user-set value."}
                                    </div>
                                </div>

                                <button
                                    className="btn"
                                    onClick={() => saveType(t)}
                                    disabled={savingType !== null}
                                >
                                    {savingType === t ? "Saving..." : "Save"}
                                </button>
                            </div>

                            <label className="field">
                                <div className="field__label">Value</div>
                                <input
                                    className="field__input"
                                    value={records[t].value}
                                    onChange={(e) => setField(t, "value", e.target.value)}
                                    placeholder={`Enter ${t} name`}
                                />
                            </label>

                            <label className="field">
                                <div className="field__label">Sensitivity</div>
                                <select
                                    className="field__input"
                                    value={records[t].sensitivity_level}
                                    onChange={(e) => setField(t, "sensitivity_level", e.target.value)}
                                >
                                    {SENS.map((s) => (
                                        <option key={s} value={s}>
                                            {s}
                                        </option>
                                    ))}
                                </select>
                            </label>
                        </div>
                    ))}
                </div>
            )}
            <Toast toast={toast} />
        </div>
    );
}