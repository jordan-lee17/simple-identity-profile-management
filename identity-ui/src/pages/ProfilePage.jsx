import { useEffect, useState } from "react";
import api from "../api/client";
import "./ProfilePage.css";

export default function ProfilePage() {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [err, setErr] = useState("");
    const [ok, setOk] = useState("");

    const [me, setMe] = useState(null);

    // user only fields
    const [personId, setPersonId] = useState(null);
    const [updatedAt, setUpdatedAt] = useState(null);
    const [legal, setLegal] = useState("");
    const [preferred, setPreferred] = useState("");
    const [professional, setProfessional] = useState("");

    async function loadMe() {
        const res = await api.get("/api/me/");
        setMe(res.data);
        setUpdatedAt(res.data.person_profile.updated_at || null);
        return res.data;
    }

    async function loadPersonProfile() {
        const res = await api.get("/api/me/profile/");
        setPersonId(res.data.person_id);

        const records = res.data.name_records || [];
        const legal = records.find((r) => r.type === "legal")?.value || "";
        const pref = records.find((r) => r.type === "preferred")?.value || "";
        const prof = records.find((r) => r.type === "professional")?.value || "";
        setLegal(legal);
        setPreferred(pref);
        setProfessional(prof);
    }

    async function load() {
        setErr("");
        setOk("");
        setLoading(true);

        try {
            const meData = await loadMe();

            if (meData.account_type === "person") {
                await loadPersonProfile();
            } else {
                setPersonId(null);
                setUpdatedAt(null);
                setPreferred("");
                setProfessional("");
            }
        } catch (e) {
            setErr("Failed to load profile. Are you logged in?");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        load();
    }, []);

    async function save(type, value) {
        setErr("");
        setOk("");
        setSaving(true);
        try {
            await api.patch("/api/me/profile/", { type, value, sensitivity_level: "low" });
            setOk(`Saved ${type}.`);
            await load();
        } catch (e) {
            const data = e?.response?.data;
            setErr(data?.detail || JSON.stringify(data) || "Save failed.");
        } finally {
            setSaving(false);
        }
    }

    if (loading) return <div className="my-names">Loading…</div>;

    // If /api/me/ doesn't load
    if (!me) return <div className="my-names">No account data.</div>;

    // requester/admin view
    if (me.account_type !== "person") {
        return (
            <div className="my-names">
                <div className="my-names-card">
                    <div className="my-names-header">
                        <h2>My Account</h2>
                        <button className="btn" onClick={load} disabled={saving}>
                            Refresh
                        </button>
                    </div>

                    <div className="meta">
                        <div>Username: <b>{me.username}</b></div>
                        <div>Email: <b>{me.email || "—"}</b></div>
                        <div>Account type: <b>{me.account_type}</b></div>

                        {me.requester && (
                            <>
                                <div>Organisation: <b>{me.requester.organisation_name}</b></div>
                                <div>Role: <b>{me.requester.role}</b></div>
                            </>
                        )}
                    </div>

                    {ok && <div className="ok">{ok}</div>}
                    {err && <div className="err">{err}</div>}
                </div>
            </div>
        );
    }

    // User view
    return (
        <div className="my-names">
            <div className="my-names-card">
                <div className="my-names-header">
                    <h2>My Names</h2>
                    <button className="btn" onClick={load} disabled={saving}>
                        Refresh
                    </button>
                </div>

                <div className="meta">
                    <div>Person ID: <b>{personId}</b></div>
                    {updatedAt && (
                        <div>
                            Last updated: <b>{new Date(updatedAt).toLocaleString()}</b>
                        </div>
                    )}
                </div>

                <div className="field">
                    <label>Legal name</label>
                    <input className="previewInput" style={{ cursor: 'not-allowed' }} disabled value={legal} onChange={(e) => setPreferred(e.target.value)}/>
                </div>

                <div className="field">
                    <label>Preferred name</label>
                    <input className="previewInput" value={preferred} onChange={(e) => setPreferred(e.target.value)} />
                    <button className="btn primary" onClick={() => save("preferred", preferred)} disabled={saving}>
                        Save preferred
                    </button>
                </div>

                <div className="field">
                    <label>Professional name</label>
                    <input className="previewInput" value={professional} onChange={(e) => setProfessional(e.target.value)} />
                    <button className="btn primary" onClick={() => save("professional", professional)} disabled={saving}>
                        Save professional
                    </button>
                </div>

                {ok && <div className="ok">{ok}</div>}
                {err && <div className="err">{err}</div>}

                <div className="note">
                    Legal name cannot be edited here. Contact an administrator if it’s incorrect.
                </div>
            </div>
        </div>
    );
}