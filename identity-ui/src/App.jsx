import { Routes, Route, Navigate } from "react-router-dom";
import { isLoggedIn } from "./auth";

import LoginPage from "./pages/LoginPage";
import Shell from "./components/Shell";
import PreviewPage from "./pages/PreviewPage";
import PoliciesPage from "./pages/PoliciesPage";
import PersonsPage from "./pages/PersonsPage";
import AuditLogsPage from "./pages/AuditLogsPage";

import "./App.css"

function RequireAuth({ children }) {
  if (!isLoggedIn()) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/"
        element={
          <RequireAuth>
            <Shell />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/preview" replace />} />
        <Route path="preview" element={<PreviewPage />} />
        <Route path="persons" element={<PersonsPage />} />
        <Route path="policies" element={<PoliciesPage />} />
        <Route path="audit-logs" element={<AuditLogsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}