import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./context/AuthContext";
import { Dashboard } from "./pages/Dashboard";
import { Deploys } from "./pages/Deploys";
import { Domains } from "./pages/Domains";
import { EnvVars } from "./pages/EnvVars";
import { Login } from "./pages/Login";
import { Logs } from "./pages/Logs";
import { Monitoring } from "./pages/Monitoring";
import { ProjectDetail } from "./pages/ProjectDetail";
import { Projects } from "./pages/Projects";
import { Settings } from "./pages/Settings";
import { Availability } from "./pages/Availability";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/:projectId" element={<ProjectDetail />} />
        <Route path="projects/:projectId/deploys" element={<Deploys />} />
        <Route path="projects/:projectId/logs" element={<Logs />} />
        <Route path="projects/:projectId/domains" element={<Domains />} />
        <Route path="projects/:projectId/env" element={<EnvVars />} />
        <Route path="projects/:projectId/monitoring" element={<Monitoring />} />
        <Route path="projects/:projectId/availability" element={<Availability />} />
        <Route path="deploys" element={<Deploys />} />
        <Route path="logs" element={<Logs />} />
        <Route path="domains" element={<Domains />} />
        <Route path="monitoring" element={<Monitoring />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
