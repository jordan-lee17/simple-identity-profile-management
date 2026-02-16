import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import "./RegisterPage.css";

export default function RegisterPage() {
    const nav = useNavigate();

    const [form, setForm] = useState({
        username: "",
        email: "",
        password: "",
        password2: "",
        legal_name: "",
        preferred_name: "",
        professional_name: "",
    });

    const [err, setErr] = useState("");
    const [success, setSuccess] = useState("");
    const [loading, setLoading] = useState(false);

    function handleChange(e) {
        const { name, value } = e.target;
        setForm((prev) => ({ ...prev, [name]: value }));
    }

    async function onSubmit(e) {
        e.preventDefault();
        setErr("");
        setSuccess("");

        if (!form.username.trim() || !form.email.trim() || !form.password) {
            setErr("Please fill in username, email, and password.");
            return;
        }
        if (!form.legal_name.trim() || !form.preferred_name || !form.professional_name) {
            setErr("All name forms are required.");
            return;
        }
        if (form.password !== form.password2) {
            setErr("Passwords do not match.");
            return;
        }

        setLoading(true);

        try {
            await api.post("/api/register/", {
                username: form.username,
                email: form.email,
                password: form.password,
                legal_name: form.legal_name,
                preferred_name: form.preferred_name,
                professional_name: form.professional_name,
            });

            setSuccess("Registration successful. Redirecting to login...");
            setTimeout(() => nav("/login"), 700);
        } catch (error) {
            setForm((prev) => ({ ...prev, password: "", password2: "" }));
            const data = error?.response?.data;
            setErr(
                data
                    ? `Registration failed: ${JSON.stringify(data)}`
                    : "Registration failed."
            );
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="register-page">
            <div className="register-card">
                <h2 className="register-title">Create Account</h2>
                <p className="register-subtitle">Register a new user account.</p>

                <form onSubmit={onSubmit} className="register-form">
                    <input
                        className="register-input"
                        name="username"
                        placeholder="username"
                        value={form.username}
                        onChange={handleChange}
                    />

                    <input
                        className="register-input"
                        name="email"
                        placeholder="email"
                        value={form.email}
                        onChange={handleChange}
                    />

                    <input
                        className="register-input"
                        name="password"
                        type="password"
                        placeholder="password"
                        value={form.password}
                        onChange={handleChange}
                    />

                    <input
                        className="register-input"
                        name="password2"
                        type="password"
                        placeholder="confirm password"
                        value={form.password2}
                        onChange={handleChange}
                    />

                    <hr />

                    <input
                        className="register-input"
                        name="legal_name"
                        placeholder="Legal Name"
                        value={form.legal_name}
                        onChange={handleChange}
                    />

                    <input
                        className="register-input"
                        name="preferred_name"
                        placeholder="Preferred Name"
                        value={form.preferred_name}
                        onChange={handleChange}
                    />

                    <input
                        className="register-input"
                        name="professional_name"
                        placeholder="Professional Name"
                        value={form.professional_name}
                        onChange={handleChange}
                    />

                    <button className="register-btn" type="submit" disabled={loading}>
                        {loading ? "Creating..." : "Create account"}
                    </button>

                    <button
                        type="button"
                        className="register-btn register-btn-secondary"
                        onClick={() => nav("/login")}
                        disabled={loading}
                    >
                        Back to login
                    </button>

                    {err && <div className="register-error">{err}</div>}
                    {success && <div className="register-ok">{success}</div>}
                </form>
            </div>
        </div>
    );
}