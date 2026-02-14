export default function SessionExpiryModal({ onExtend, onLogout }) {
  return (
    <div style={overlay}>
      <div style={modal}>
        <h3>Session Expiring</h3>
        <p>Your session will expire soon. Extend session?</p>

        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={onExtend}>Extend</button>
          <button onClick={onLogout}>Logout</button>
        </div>
      </div>
    </div>
  );
}

const overlay = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.6)",
  display: "grid",
  placeItems: "center",
};

const modal = {
  background: "#0f1a33",
  padding: 20,
  borderRadius: 12,
  color: "white",
};