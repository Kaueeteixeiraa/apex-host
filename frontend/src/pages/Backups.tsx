import { useEffect, useState } from "react";
import { DatabaseBackup, Download, RefreshCcw, RotateCcw, ShieldCheck } from "lucide-react";

import { EmptyState } from "../components/EmptyState";
import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { API_BASE_URL, api, BackupRecord, formatDate, getToken } from "../lib/api";

export function Backups() {
  const [items, setItems] = useState<BackupRecord[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setItems(await api<BackupRecord[]>("/backups"));
    setLoading(false);
  };

  useEffect(() => {
    void load().catch((err) => {
      setError(err instanceof Error ? err.message : "Erro ao carregar backups");
      setLoading(false);
    });
  }, []);

  const createBackup = async () => {
    try {
      setError(null);
      setMessage(null);
      const backup = await api<BackupRecord>("/backups/export", { method: "POST" });
      setMessage(`Backup #${backup.id} gerado com sucesso.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar backup");
    }
  };

  const restoreBackup = async (backup: BackupRecord) => {
    const confirmation = window.prompt(`Digite RESTAURAR para preparar restore do backup #${backup.id}`);
    if (confirmation !== "RESTAURAR") return;
    await api(`/backups/${backup.id}/restore`, {
      method: "POST",
      body: JSON.stringify({ confirmation })
    });
    setMessage(`Restore do backup #${backup.id} preparado e auditado.`);
  };

  const downloadBackup = async (backup: BackupRecord) => {
    const response = await fetch(`${API_BASE_URL}/backups/${backup.id}/download`, {
      headers: { Authorization: `Bearer ${getToken() || ""}` }
    });
    if (!response.ok) throw new Error("Nao foi possivel baixar o backup");
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `apex-backup-${backup.id}.json`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  const last = items[0];
  const next = last ? nextBackupLabel(last.created_at) : "Aguardando primeiro backup";

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Recuperacao operacional"
        title="Backups"
        description="Backups internos de banco, projetos, dominios, envs criptografadas e metadados de deploy."
        icon={DatabaseBackup}
        actions={
          <button className="btn-primary" onClick={() => void createBackup()}>
            <RefreshCcw className="h-4 w-4" />
            Gerar backup agora
          </button>
        }
      />

      {message ? <FeedbackBanner type="success" message={message} /> : null}
      {error ? <FeedbackBanner type="error" message={error} /> : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Ultimo backup" value={last ? `#${last.id}` : "-"} icon={DatabaseBackup} detail={last ? formatDate(last.created_at) : "Nenhum backup"} />
        <StatCard title="Proximo backup" value={next} icon={ShieldCheck} detail="Rotina diaria recomendada" />
        <StatCard title="Status" value={last?.status || "sem backup"} icon={RefreshCcw} />
        <StatCard title="Tamanho" value={last?.size_bytes ? formatBytes(last.size_bytes) : "-"} icon={Download} detail={last?.backup_type || "completo"} />
      </section>

      <section className="panel p-4">
        <h2 className="mb-4 font-semibold text-white">Lista de backups</h2>
        {loading ? <div className="skeleton-shimmer h-24 rounded-md" /> : null}
        {!loading && items.length === 0 ? (
          <EmptyState
            icon={DatabaseBackup}
            title="Nenhum backup registrado"
            description="Gere o primeiro backup para validar a rotina de recuperacao da infraestrutura Apex."
            action={
              <button className="btn-primary" onClick={() => void createBackup()}>
                Gerar backup agora
              </button>
            }
          />
        ) : null}
        <div className="space-y-3">
          {items.map((backup) => (
            <div key={backup.id} className="flex flex-col gap-3 rounded-md border border-apex-line bg-white/[0.03] p-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="flex items-center gap-2 text-sm text-white">
                  Backup #{backup.id}
                  <StatusBadge status={backup.status} />
                </div>
                <div className="mt-1 text-xs text-apex-muted">
                  {formatDate(backup.created_at)} | {backup.backup_type} | {backup.size_bytes ? formatBytes(backup.size_bytes) : "tamanho pendente"}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button className="btn-secondary" onClick={() => void downloadBackup(backup).catch((err) => setError(err instanceof Error ? err.message : "Erro ao baixar backup"))}>
                  <Download className="h-4 w-4" />
                  Baixar
                </button>
                <button className="btn-danger" onClick={() => void restoreBackup(backup)}>
                  <RotateCcw className="h-4 w-4" />
                  Restaurar
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function formatBytes(value: number) {
  if (value < 1024 * 1024) return `${Math.round(value / 1024)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

function nextBackupLabel(createdAt: string) {
  const date = new Date(createdAt);
  date.setDate(date.getDate() + 1);
  return formatDate(date.toISOString());
}

