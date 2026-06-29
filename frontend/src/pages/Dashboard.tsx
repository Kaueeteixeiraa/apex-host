import { useEffect, useState } from "react";
import { Activity, AlertTriangle, Boxes, Cpu, Globe2, HardDrive, MemoryStick, Rocket } from "lucide-react";
import { Link } from "react-router-dom";

import { api, DashboardStats, formatDate } from "../lib/api";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";

export function Dashboard() {
  const [data, setData] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<DashboardStats>("/dashboard")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar dashboard"));
  }, []);

  if (error) return <div className="panel p-5 text-red-200">{error}</div>;
  if (!data) return <div className="panel p-5 text-apex-muted">Carregando dashboard...</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="muted mt-1">Visao geral dos projetos, deploys e saude da VPS.</p>
        </div>
        <Link to="/projects" className="btn-primary">
          <Rocket className="h-4 w-4" />
          Novo projeto
        </Link>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Total de projetos" value={data.total_projects} icon={Boxes} detail={`${data.online_projects} online`} />
        <StatCard title="Dominios ativos" value={data.active_domains} icon={Globe2} detail="Custom + subdominios" />
        <StatCard title="Erros recentes" value={data.recent_errors} icon={AlertTriangle} detail="Entradas de log do tipo erro" />
        <StatCard title="CPU do servidor" value={`${data.server.cpu_percent}%`} icon={Cpu} detail="Leitura instantanea" />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="panel p-4">
          <div className="mb-4 flex items-center gap-2 text-white">
            <MemoryStick className="h-5 w-5 text-apex-cyan" />
            RAM
          </div>
          <div className="h-2 rounded-full bg-white/10">
            <div className="h-2 rounded-full bg-apex-cyan" style={{ width: `${data.server.memory_percent}%` }} />
          </div>
          <p className="muted mt-3">
            {data.server.memory_used_gb} GB de {data.server.memory_total_gb} GB
          </p>
        </div>
        <div className="panel p-4">
          <div className="mb-4 flex items-center gap-2 text-white">
            <HardDrive className="h-5 w-5 text-apex-blue" />
            Armazenamento
          </div>
          <div className="h-2 rounded-full bg-white/10">
            <div className="h-2 rounded-full bg-apex-blue" style={{ width: `${data.server.disk_percent}%` }} />
          </div>
          <p className="muted mt-3">
            {data.server.disk_used_gb} GB de {data.server.disk_total_gb} GB
          </p>
        </div>
        <div className="panel p-4">
          <div className="mb-4 flex items-center gap-2 text-white">
            <Activity className="h-5 w-5 text-emerald-300" />
            Status
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-md border border-apex-line p-3">
              <div className="text-apex-muted">Offline</div>
              <div className="mt-1 text-xl text-white">{data.offline_projects}</div>
            </div>
            <div className="rounded-md border border-apex-line p-3">
              <div className="text-apex-muted">Buildando</div>
              <div className="mt-1 text-xl text-white">{data.building_projects}</div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="panel p-4">
          <h2 className="mb-4 font-semibold text-white">Ultimos deploys</h2>
          <div className="space-y-3">
            {data.recent_deploys.length === 0 ? <p className="muted">Nenhum deploy ainda.</p> : null}
            {data.recent_deploys.map((deploy) => (
              <div key={deploy.id} className="flex items-center justify-between rounded-md border border-apex-line p-3">
                <div>
                  <div className="text-sm text-white">Deploy #{deploy.id}</div>
                  <div className="text-xs text-apex-muted">{formatDate(deploy.started_at)}</div>
                </div>
                <StatusBadge status={deploy.status} />
              </div>
            ))}
          </div>
        </div>
        <div className="panel p-4">
          <h2 className="mb-4 font-semibold text-white">Erros recentes</h2>
          <div className="space-y-3">
            {data.recent_logs.length === 0 ? <p className="muted">Sem erros recentes.</p> : null}
            {data.recent_logs.map((log) => (
              <div key={log.id} className="rounded-md border border-red-500/20 bg-red-500/5 p-3">
                <div className="text-xs text-apex-muted">{formatDate(log.created_at)}</div>
                <div className="mt-1 text-sm text-red-100">{log.message}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
