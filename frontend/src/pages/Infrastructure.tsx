import { useEffect, useState } from "react";
import { Activity, AlertTriangle, Cpu, Database, Gauge, Globe2, HardDrive, MemoryStick, RefreshCcw, Server } from "lucide-react";

import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { api, formatDate, InfrastructureStatus } from "../lib/api";

export function Infrastructure() {
  const [data, setData] = useState<InfrastructureStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => setData(await api<InfrastructureStatus>("/monitor/infrastructure"));

  useEffect(() => {
    void load().catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar infraestrutura"));
  }, []);

  if (error) return <FeedbackBanner type="error" message={error} />;

  const uptime = data?.server.uptime_seconds ? formatUptime(data.server.uptime_seconds) : "-";

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Servidores Apex"
        title="Infraestrutura"
        description="Operacao 24/7 da VPS, servicos internos, containers e alertas."
        icon={Server}
        actions={
          <button className="btn-secondary" onClick={() => void load()}>
            <RefreshCcw className="h-4 w-4" />
            Atualizar
          </button>
        }
      />

      {data?.dry_run ? (
        <div className="panel border-yellow-400/30 bg-yellow-400/5 p-4">
          <div className="font-semibold text-yellow-100">DRY RUN ATIVO</div>
          <p className="muted mt-1">Deploys reais com Docker estao desativados. Este ambiente e seguro para testes locais.</p>
        </div>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Status geral" value={data?.overall_status || "..."} icon={Gauge} detail={data?.environment || "local"} />
        <StatCard title="CPU" value={data ? `${data.server.cpu_percent}%` : "..."} icon={Cpu} />
        <StatCard title="RAM" value={data ? `${data.server.memory_percent}%` : "..."} icon={MemoryStick} detail={data ? `${data.server.memory_used_gb}/${data.server.memory_total_gb} GB` : undefined} />
        <StatCard title="Disco" value={data ? `${data.server.disk_percent}%` : "..."} icon={HardDrive} detail={data?.server.disk_free_gb ? `${data.server.disk_free_gb} GB livres` : undefined} />
        <StatCard title="Uptime" value={uptime} icon={Activity} />
        <StatCard title="Containers ativos" value={data?.docker.active_containers ?? "..."} icon={Server} detail={data?.docker.available ? "Docker disponivel" : "Docker indisponivel"} />
        <StatCard title="Certbot/SSL" value={data?.services.certbot || "..."} icon={Globe2} />
        <StatCard title="Alertas recentes" value={data?.alerts.length ?? "..."} icon={AlertTriangle} />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="panel p-4">
          <h2 className="mb-4 font-semibold text-white">Servicos internos</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(data?.services || {}).map(([name, status]) => (
              <div key={name} className="flex items-center justify-between rounded-md border border-apex-line bg-white/[0.03] p-3">
                <div className="flex items-center gap-2 text-sm text-white">
                  <Database className="h-4 w-4 text-apex-cyan" />
                  {name}
                </div>
                <StatusBadge status={status} />
              </div>
            ))}
          </div>
        </div>

        <div className="panel p-4">
          <h2 className="mb-4 font-semibold text-white">Ultimos alertas</h2>
          <div className="space-y-3">
            {!data?.alerts.length ? <p className="muted">Nenhum alerta recente.</p> : null}
            {data?.alerts.map((alert) => (
              <div key={alert.id} className="rounded-md border border-apex-line bg-white/[0.03] p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-white">{alert.message}</span>
                  <StatusBadge status={alert.severity} />
                </div>
                <div className="mt-1 text-xs text-apex-muted">{formatDate(alert.created_at)}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function formatUptime(seconds: number) {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  return days > 0 ? `${days}d ${hours}h` : `${hours}h`;
}
