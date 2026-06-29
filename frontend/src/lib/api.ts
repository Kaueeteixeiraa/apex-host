const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  plan: string;
  is_active: boolean;
  limits: Record<string, unknown>;
  created_at: string;
};

export type Project = {
  id: number;
  owner_id: number;
  name: string;
  slug: string;
  github_url: string | null;
  branch: string;
  project_type: string;
  install_command: string | null;
  build_command: string | null;
  start_command: string | null;
  internal_port: number;
  host_port: number | null;
  primary_domain: string | null;
  auto_subdomain: string;
  status: string;
  last_deploy_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Deploy = {
  id: number;
  project_id: number;
  status: string;
  branch: string;
  commit_sha: string | null;
  duration_seconds: number | null;
  logs: string | null;
  error: string | null;
  dry_run: boolean;
  started_at: string;
  finished_at: string | null;
};

export type Domain = {
  id: number;
  project_id: number;
  hostname: string;
  is_primary: boolean;
  ssl_enabled: boolean;
  dns_status: string;
  created_at: string;
};

export type EnvVar = {
  id: number;
  project_id: number;
  key: string;
  is_secret: boolean;
  masked_value: string;
  created_at: string;
  updated_at: string;
};

export type LogEntry = {
  id: number;
  project_id: number;
  deploy_id: number | null;
  type: string;
  message: string;
  created_at: string;
};

export type ServerMetric = {
  cpu_percent: number;
  memory_percent: number;
  memory_used_gb: number;
  memory_total_gb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
};

export type DashboardStats = {
  total_projects: number;
  online_projects: number;
  offline_projects: number;
  building_projects: number;
  error_projects: number;
  active_domains: number;
  recent_errors: number;
  server: ServerMetric;
  recent_deploys: Deploy[];
  recent_logs: LogEntry[];
};

export function getToken() {
  return localStorage.getItem("apex_host_token");
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem("apex_host_token", token);
  else localStorage.removeItem("apex_host_token");
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {
      detail = await response.text();
    }
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const formatDate = (value: string | null) =>
  value ? new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value)) : "-";
