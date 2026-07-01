const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
export const API_BASE_URL = API_URL;

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  access_profile: string;
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
  github_repo_full_name: string | null;
  github_webhook_id: string | null;
  github_webhook_enabled: boolean;
  cpu_limit: string | null;
  memory_limit: string | null;
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
  commit_author: string | null;
  commit_message: string | null;
  deploy_type: string;
  queue_job_id: string | null;
  duration_seconds: number | null;
  logs: string | null;
  error: string | null;
  dry_run: boolean;
  cancel_requested_at: string | null;
  started_at: string;
  finished_at: string | null;
};

export type Domain = {
  id: number;
  project_id: number;
  hostname: string;
  is_primary: boolean;
  ssl_enabled: boolean;
  ssl_status: string;
  ssl_expires_at: string | null;
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
  disk_free_gb?: number;
  uptime_seconds?: number;
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
  recent_projects: Project[];
};

export type InfrastructureStatus = {
  overall_status: "stable" | "attention" | "critical" | string;
  environment: string;
  deploy_stage?: string;
  deploy_mode: string;
  dry_run: boolean;
  server: ServerMetric;
  services: Record<string, string>;
  docker: {
    available: boolean;
    active_containers: number;
    containers: string[];
  };
  alerts: Alert[];
};

export type GitHubRepo = {
  full_name: string;
  clone_url: string;
  default_branch: string;
  private: boolean;
};

export type GitHubConnection = {
  connected: boolean;
  login: string | null;
  scope: string | null;
  connected_at: string | null;
};

export type EnvVarReveal = {
  id: number;
  key: string;
  value: string;
  expires_in_seconds: number;
};

export type AuditLog = {
  id: number;
  user_id: number | null;
  project_id: number | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  ip_address: string | null;
  details: Record<string, unknown>;
  created_at: string;
};

export type AvailabilitySettings = {
  id: number;
  project_id: number;
  health_check_path: string;
  health_check_url: string | null;
  high_availability_enabled: boolean;
  auto_restart_enabled: boolean;
  auto_rollback_enabled: boolean;
  blue_green_enabled: boolean;
  static_fallback_enabled: boolean;
  cdn_fallback_enabled: boolean;
  fallback_title: string;
  fallback_message: string;
  max_restart_attempts: number;
  restart_attempts: number;
  last_restart_at: string | null;
  degraded_reason: string | null;
  backup_enabled: boolean;
  last_backup_at: string | null;
  created_at: string;
  updated_at: string;
};

export type HealthCheck = {
  id: number;
  project_id: number;
  status: string;
  http_status: number | null;
  response_time_ms: number | null;
  error: string | null;
  checked_at: string;
};

export type ServerNode = {
  id: number;
  name: string;
  role: string;
  base_url: string | null;
  status: string;
  cpu_capacity: string | null;
  ram_capacity: string | null;
  last_seen_at: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type Alert = {
  id: number;
  project_id: number | null;
  severity: string;
  event_type: string;
  message: string;
  acknowledged: boolean;
  created_at: string;
};

export type BackupRecord = {
  id: number;
  project_id: number | null;
  backup_type: string;
  status: string;
  path: string | null;
  size_bytes: number | null;
  error: string | null;
  created_at: string;
};

export type AvailabilitySummary = {
  settings: AvailabilitySettings;
  last_check: HealthCheck | null;
  uptime_24h: number;
  uptime_7d: number;
  average_response_ms: number | null;
  recent_checks: HealthCheck[];
  recent_alerts: Alert[];
  nodes: ServerNode[];
  backups: BackupRecord[];
  stable_deploy: Deploy | null;
  ha_warning: string | null;
};

export type ProjectTemplate = {
  id: string;
  name: string;
  description: string;
  stack: string;
  install_command: string | null;
  build_command: string | null;
  start_command: string | null;
  output_directory: string | null;
  internal_port: number;
  project_type: string;
  icon: string;
  preview: string;
  tags: string[];
};

export type FrameworkDetection = {
  framework: string;
  project_type: string;
  build_command: string | null;
  start_command: string | null;
  install_command: string | null;
  output_directory: string | null;
  default_port: number;
  runtime: string;
  confidence: number;
  reasons: string[];
};

export type LogAnalysis = {
  summary: string;
  possible_cause: string;
  suggested_fix: string;
  severity: string;
  important_lines: string[];
  signals: string[];
  provider: string;
};

export type PlatformSettings = {
  id: number;
  platform_name: string;
  logo_url: string | null;
  primary_color: string;
  primary_domain: string | null;
  maintenance_mode: boolean;
  allow_registration: boolean;
  require_account_approval: boolean;
  default_user_profile: string;
  default_user_limits: Record<string, unknown>;
  smtp_config: Record<string, unknown>;
  alert_config: Record<string, unknown>;
  backup_config: Record<string, unknown>;
  cdn_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type UserSession = {
  id: number;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  last_seen_at: string | null;
  revoked_at: string | null;
};

export type AdminOverview = {
  stats: Record<string, number>;
  users: User[];
  projects: Project[];
  deploys: Deploy[];
  alerts: Alert[];
  audit_logs: AuditLog[];
  nodes: ServerNode[];
  recent_errors: LogEntry[];
};

export type PublicComponentStatus = {
  name: string;
  status: string;
  detail: string;
};

export type PublicStatus = {
  overall_status: string;
  uptime_24h: number;
  uptime_7d: number;
  components: PublicComponentStatus[];
  incidents: Alert[];
  recent_checks: HealthCheck[];
  platform: Record<string, unknown>;
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
