import "./Toast.css";

export default function Toast({ toast }) {
  if (!toast) return null;

  return (
    <div className={`toast ${toast.variant === "ok" ? "toastOk" : "toastWarn"}`}>
      <div className="toastTitle">{toast.title}</div>
      <div className="toastBody">{toast.body}</div>
    </div>
  );
}