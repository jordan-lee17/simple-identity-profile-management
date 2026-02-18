import { Routes, Route, Navigate } from "react-router-dom";
import { isLoggedIn } from "./auth";

import LoginPage from "./pages/LoginPage";
import Shell from "./components/Shell";
import PreviewPage from "./pages/PreviewPage";
import PoliciesPage from "./pages/PoliciesPage";
import PersonsPage from "./pages/PersonsPage";
import RequesterPage from "./pages/RequesterPage";
import AuditLogsPage from "./pages/AuditLogsPage";
import RegisterPage from "./pages/RegisterPage";
import ProfilePage from "./pages/ProfilePage";
import AdminPersonEditPage from "./pages/AdminEditPersonPage";
import HomeRedirect from "./pages/HomeRedirect";
import RequireAccountType from "./components/RequireAccountType"

import "./App.css"

function RequireAuth({ children }) {
  if (!isLoggedIn()) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        path="/"
        element={
          <RequireAuth>
            <Shell />
          </RequireAuth>
        }
      >
        {/* Default Page */}
        <Route index element={<HomeRedirect />} />

        <Route
          path="preview"
          element={
            <RequireAccountType allowedTypes={["requester", "admin"]}>
              <PreviewPage />
            </RequireAccountType>
          }
        />

        <Route
          path="policies"
          element={
            <RequireAccountType allowedTypes={["admin"]}>
              <PoliciesPage />
            </RequireAccountType>
          }
        />
        <Route
          path="persons"
          element={
            <RequireAccountType allowedTypes={["admin"]}>
              <PersonsPage />
            </RequireAccountType>
          }
        />
        <Route
          path="persons/:personId"
          element={
            <RequireAccountType allowedTypes={["admin"]}>
              <AdminPersonEditPage />
            </RequireAccountType>
          }
        />
        <Route
          path="requesters"
          element={
            <RequireAccountType allowedTypes={["admin"]}>
              <RequesterPage />
            </RequireAccountType>
          }
        />
        <Route
          path="audit-logs"
          element={
            <RequireAccountType allowedTypes={["admin"]}>
              <AuditLogsPage />
            </RequireAccountType>
          }
        />

        <Route
          path="profile"
          element={
            <RequireAccountType allowedTypes={["person", "requester"]}>
              <ProfilePage />
            </RequireAccountType>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}