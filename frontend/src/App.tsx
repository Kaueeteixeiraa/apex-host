import { Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./context/AuthContext";
import { Dashboard } from "./pages/Dashboard";
import { Deploys } from "./pages/Deploys";
import { Domains } from "./pages/Domains";
import { EnvVars } from "./pages/EnvVars";
import { Help } from "./pages/Help";
import { Login } from "./pages/Login";
import { Logs } from "./pages/Logs";
import { Monitoring } from "./pages/Monitoring";
import { NotFound } from "./pages/NotFound";
import { Plans } from "./pages/Plans";
import { ProjectDetail } from "./pages/ProjectDetail";
import { Projects } from "./pages/Projects";
import { PublicStatus } from "./pages/PublicStatus";
import { Settings } from "./pages/Settings";
import { Support } from "./pages/Support";
import { Availability } from "./pages/Availability";
import { Admin } from "./pages/Admin";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/status" element={<PublicStatus />} />
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
        <Route path="plans" element={<Plans />} />
        <Route path="deploys" element={<Deploys />} />
        <Route path="logs" element={<Logs />} />
        <Route path="domains" element={<Domains />} />
        <Route path="monitoring" element={<Monitoring />} />
        <Route path="support" element={<Support />} />
        <Route path="help" element={<Help />} />
        <Route path="admin" element={<Admin />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
