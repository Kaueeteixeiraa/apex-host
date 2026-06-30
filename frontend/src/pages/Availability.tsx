import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { AlertTriangle, DatabaseBackup, type LucideIcon, RefreshCcw, Server, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

import { Alert, api, API_BASE_URL, AvailabilitySummary, BackupRecord, formatDate, getToken, HealthCheck } from "../lib/api";
import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
import { ProjectTabs } from "../components/ProjectTabs";
import { StatusBadge } from "../components/StatusBadge";

export function Availability() {
  const { projectId } = useParams();
  const [data, setData] = useState<AvailabilitySummary | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    if (!projectId) return;
    setData(await api<AvailabilitySummary>(`/projects/${projectId}/availability`));
  };

  useEffect(() => {
    void load().catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar disponibilidade"));
  }, [projectId]);

  const runCheck = async () => {
    if (!projectId) return;
    await api<HealthCheck>(`/projects/${projectId}/availability/check`, { method: "POST" });
    setMessage("Health check executado.");
    await load();
  };

  const exportBackup = async () => {
    if (!projectId) return;
    const backup = await api<BackupRecord>(`/projects/${projectId}/backups/export`, { method: "POST" });
    setMessage(`Backup exportado: ${backup.path}`);
    await load();
  };

  const downloadBackup = async (backup: BackupRecord) => {
    const response = await fetch(`${API_BASE_URL}/backups/${backup.id}/download`, {
      headers: { Authorization: `Bearer ${getToken() || ""}` }
    });
    if (!response.ok) throw new Error("Erro ao baixar backup");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = backup.path?.split(/[\\/]/).pop() || `apex-backup-${backup.id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const restoreBackup = async (backup: BackupRecord) => {
    const confirmation = prompt("Digite RESTAURAR para preparar a restauracao deste backup.");
    if (confirmation !== "RESTAURAR") return;
    await api(`/backups/${backup.id}/restore`, { method: "POST", body: JSON.stringify({ confirmation }) });
    setMessage("Restore preparado e registrado em auditoria. Execucao destrutiva segue desativada por seguranca.");
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (!projectId || !data) return;
    setSaving(true);
    setMessage(null);
    try {
      await api(`/projects/${projectId}/availability/settings`, {
        method: "PATCH",
        body: JSON.stringify({
          health_check_path: data.settings.health_check_path,
          health_check_url: data.settings.health_check_url || null,
          high_availability_enabled: data.settings.high_availability_enabled,
          auto_restart_enabled: data.settings.auto_restart_enabled,
          auto_rollback_enabled: data.settings.auto_rollback_enabled,
          blue_green_enabled: data.settings.blue_green_enabled,
          static_fallback_enabled: data.settings.static_fallback_enabled,
          cdn_fallback_enabled: data.settings.cdn_fallback_enabled,
          fallback_title: data.settings.fallback_title,
          fallback_message: data.settings.fallback_message,
          max_restart_attempts: data.settings.max_restart_attempts,
          backup_enabled: data.settings.backup_enabled
        })
      });
      setMessage("Configuracoes de disponibilidade salvas.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar disponibilidade");
    } finally {
      setSaving(false);
    }
  };

  if (error) return <FeedbackBanner type="error" message={error} />;
  if (!data) return <div className="panel p-5 text-apex-muted">Carregando disponibilidade...</div>;

  const lastStatus = data.last_check?.status || "unknown";

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="High Availability"
        title="Disponibilidade"
        description="Health checks, auto-restart, rollback automatico, backups, nodes e preparo para redundancia real."
        icon={ShieldCheck}
        actions={
          <>
            <button className="btn-secondary" onClick={() => void runCheck()}>
              <RefreshCcw className="h-4 w-4" />
              Health check
            </button>
            <button className="btn-primary" onClick={() => void exportBackup()}>
              <DatabaseBackup className="h-4 w-4" />
              Exportar backup
            </button>
          </>
        }
      />
      <ProjectTabs projectId={Number(projectId)} />
      {message ? <FeedbackBanner type="success" message={message} /> : null}
      {data.ha_warning ? <FeedbackBanner type="info" message={data.ha_warning} /> : null}

      <section className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Status atual" value={<StatusBadge status={lastStatus === "unknown" ? "offline" : lastStatus} />} />
        <MetricCard title="Uptime 24h" value={`${data.uptime_24h}%`} />
        <MetricCard title="Uptime 7 dias" value={`${data.uptime_7d}%`} />
        <MetricCard title="Resposta media" value={data.average_response_ms ? `${data.average_response_ms}ms` : "-"} />
      </section>

      <section className="panel p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-semibold text-white">Historico simples de uptime</h2>
          <span className="text-xs text-apex-muted">{data.recent_checks.length} checks recentes</span>
        </div>
        <div className="flex flex-wrap gap-1">
          {data.recent_checks.slice().reverse().map((check) => (
            <span
              key={check.id}
              title={`${formatDate(check.checked_at)} - ${check.status} - ${check.response_time_ms || "-"}ms`}
              className={`h-8 w-2 rounded-full ${
                check.status === "online" ? "bg-emerald-400 shadow-[0_0_14px_rgba(52,211,153,0.55)]" : check.status === "degraded" ? "bg-amber-300" : "bg-red-400"
              }`}
            />
          ))}
          {data.recent_checks.length === 0 ? <p className="muted">Nenhum health check registrado ainda.</p> : null}
        </div>
      </section>

      <form className="panel grid gap-4 p-4 lg:grid-cols-2" onSubmit={save}>
        <div className="space-y-4">
          <label>
            <span className="label">Health check path</span>
            <input
              className="field"
              value={data.settings.health_check_path}
              onChange={(event) => setData({ ...data, settings: { ...data.settings, health_check_path: event.target.value } })}
            />
          </label>
          <label>
            <span className="label">Health check URL opcional</span>
            <input
              className="field"
              value={data.settings.health_check_url || ""}
              onChange={(event) => setData({ ...data, settings: { ...data.settings, health_check_url: event.target.value } })}
              placeholder="https://app.exemplo.com/health"
            />
          </label>
          <label>
            <span className="label">Max restart attempts</span>
            <input
              className="field"
              type="number"
              value={data.settings.max_restart_attempts}
              onChange={(event) => setData({ ...data, settings: { ...data.settings, max_restart_attempts: Number(event.target.value) } })}
            />
          </label>
        </div>
        <div className="grid gap-3">
          <Toggle label="Alta disponibilidade" checked={data.settings.high_availability_enabled} onChange={(checked) => setData({ ...data, settings: { ...data.settings, high_availability_enabled: checked } })} />
          <Toggle label="Auto-restart" checked={data.settings.auto_restart_enabled} onChange={(checked) => setData({ ...data, settings: { ...data.settings, auto_restart_enabled: checked } })} />
          <Toggle label="Rollback automatico" checked={data.settings.auto_rollback_enabled} onChange={(checked) => setData({ ...data, settings: { ...data.settings, auto_rollback_enabled: checked } })} />
          <Toggle label="Blue/green deploy" checked={data.settings.blue_green_enabled} onChange={(checked) => setData({ ...data, settings: { ...data.settings, blue_green_enabled: checked } })} />
          <Toggle label="Fallback estatico/CDN" checked={data.settings.static_fallback_enabled} onChange={(checked) => setData({ ...data, settings: { ...data.settings, static_fallback_enabled: checked } })} />
          <Toggle label="CDN externa" checked={data.settings.cdn_fallback_enabled} onChange={(checked) => setData({ ...data, settings: { ...data.settings, cdn_fallback_enabled: checked } })} />
        </div>
        <label className="lg:col-span-2">
          <span className="label">Titulo da pagina fallback</span>
          <input
            className="field"
            value={data.settings.fallback_title}
            onChange={(event) => setData({ ...data, settings: { ...data.settings, fallback_title: event.target.value } })}
          />
        </label>
        <label className="lg:col-span-2">
          <span className="label">Mensagem fallback</span>
          <textarea
            className="field min-h-24"
            value={data.settings.fallback_message}
            onChange={(event) => setData({ ...data, settings: { ...data.settings, fallback_message: event.target.value } })}
          />
        </label>
        <div className="lg:col-span-2">
          <button className="btn-primary" disabled={saving}>
            {saving ? "Salvando..." : "Salvar disponibilidade"}
          </button>
        </div>
      </form>

      <section className="grid gap-4 lg:grid-cols-3">
        <Panel title="Nodes" icon={Server}>
          {data.nodes.map((node) => (
            <div key={node.id} className="rounded-md border border-apex-line bg-black/20 p-3">
              <div className="flex items-center justify-between">
                <span className="font-medium text-white">{node.name}</span>
                <StatusBadge status={node.status} />
              </div>
              <p className="mt-1 text-xs text-apex-muted">
                {node.role} - CPU {node.cpu_capacity || "-"} - RAM {node.ram_capacity || "-"}
              </p>
            </div>
          ))}
        </Panel>
        <Panel title="Alertas" icon={AlertTriangle}>
          {data.recent_alerts.map((alert: Alert) => (
            <div key={alert.id} className="rounded-md border border-apex-line bg-black/20 p-3">
              <div className="text-sm font-medium text-white">{alert.event_type}</div>
              <p className="mt-1 text-xs text-apex-muted">{alert.message}</p>
              <p className="mt-2 text-xs text-apex-muted">{formatDate(alert.created_at)}</p>
            </div>
          ))}
          {data.recent_alerts.length === 0 ? <p className="muted">Nenhum alerta recente.</p> : null}
        </Panel>
        <Panel title="Backups" icon={DatabaseBackup}>
          {data.backups.map((backup) => (
            <div key={backup.id} className="rounded-md border border-apex-line bg-black/20 p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-medium text-white">{backup.backup_type}</div>
                  <p className="mt-1 truncate text-xs text-apex-muted">{backup.path || backup.status}</p>
                  <p className="mt-2 text-xs text-apex-muted">
                    {formatDate(backup.created_at)} - {backup.size_bytes ? `${Math.round(backup.size_bytes / 1024)} KB` : "tamanho n/a"}
                  </p>
                </div>
                <StatusBadge status={backup.status} />
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button className="btn-secondary" onClick={() => void downloadBackup(backup)}>Baixar</button>
                <button className="btn-danger" onClick={() => void restoreBackup(backup)}>Restaurar</button>
              </div>
            </div>
          ))}
          {data.backups.length === 0 ? <p className="muted">Nenhum backup registrado.</p> : null}
        </Panel>
      </section>
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string | JSX.Element }) {
  return (
    <div className="panel p-4">
      <div className="text-xs uppercase tracking-[0.12em] text-apex-muted">{title}</div>
      <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="flex items-center justify-between rounded-md border border-apex-line bg-black/20 p-3 text-sm text-apex-text">
      {label}
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
    </label>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: ReactNode }) {
  return (
    <div className="panel space-y-3 p-4">
      <div className="mb-2 flex items-center gap-2 font-semibold text-white">
        <Icon className="h-5 w-5 text-apex-cyan" />
        {title}
      </div>
      {children}
    </div>
  );
}
