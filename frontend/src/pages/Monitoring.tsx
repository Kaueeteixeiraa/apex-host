import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Activity, Boxes, Cpu, Database, HardDrive, MemoryStick, RefreshCcw, Server } from "lucide-react";

import { api, DashboardStats, InfrastructureStatus, ServerMetric } from "../lib/api";
import { StatCard } from "../components/StatCard";
import { ProjectSelector } from "../components/ProjectSelector";
import { ProjectTabs } from "../components/ProjectTabs";
import { StatusBadge } from "../components/StatusBadge";
import { useProjectScope } from "../lib/useProjectScope";

export function Monitoring() {
  const { projectId } = useParams();
  const { projects, selectedId, selectedProject, setSelectedId, loading, error } = useProjectScope(projectId);
  const [server, setServer] = useState<ServerMetric | null>(null);
  const [infra, setInfra] = useState<InfrastructureStatus | null>(null);
  const [dashboard, setDashboard] = useState<DashboardStats | null>(null);
  const [projectMetric, setProjectMetric] = useState<Record<string, unknown> | null>(null);

  const load = async () => {
    const [serverMetric, infraStatus, dashboardStats] = await Promise.all([
      api<ServerMetric>("/monitor/server"),
      api<InfrastructureStatus>("/monitor/infrastructure"),
      api<DashboardStats>("/dashboard")
    ]);
    setServer(serverMetric);
    setInfra(infraStatus);
    setDashboard(dashboardStats);
    if (selectedId) setProjectMetric(await api<Record<string, unknown>>(`/monitor/projects/${selectedId}`));
  };

  useEffect(() => {
    void load();
    const interval = window.setInterval(() => void load(), 5000);
    return () => window.clearInterval(interval);
  }, [selectedId]);

  if (error) return <div className="panel p-5 text-red-200">{error}</div>;

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="page-title">Monitoramento</h1>
          <p className="muted mt-1">Metricas da VPS, servicos internos, containers e projetos hospedados.</p>
        </div>
        <button className="btn-secondary" onClick={() => void load()}>
          <RefreshCcw className="h-4 w-4" />
          Atualizar
        </button>
      </div>
      {selectedProject ? <ProjectTabs projectId={selectedProject.id} /> : null}
      {server ? (
        <section className="grid gap-4 md:grid-cols-3">
          <StatCard title="CPU" value={`${server.cpu_percent}%`} icon={Cpu} />
          <StatCard title="RAM" value={`${server.memory_percent}%`} icon={MemoryStick} detail={`${server.memory_used_gb}/${server.memory_total_gb} GB`} />
          <StatCard title="Disco" value={`${server.disk_percent}%`} icon={HardDrive} detail={`${server.disk_used_gb}/${server.disk_total_gb} GB`} />
        </section>
      ) : null}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Projetos online" value={dashboard?.online_projects ?? 0} icon={Boxes} detail={`${dashboard?.offline_projects ?? 0} offline`} />
        <StatCard title="Containers ativos" value={infra?.docker.active_containers ?? 0} icon={Server} detail={infra?.docker.available ? "Docker acessivel" : "Docker indisponivel"} />
        <StatCard title="Banco" value={infra?.services.postgresql || "unknown"} icon={Database} detail="PostgreSQL" />
        <StatCard title="Worker" value={infra?.services.worker || "unknown"} icon={Activity} detail={`Nginx: ${infra?.services.nginx || "unknown"}`} />
      </section>
      {infra ? (
        <div className="panel p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <h2 className="font-semibold text-white">Servicos internos</h2>
              <p className="text-sm text-apex-muted">Saude geral do ambiente {infra.environment}.</p>
            </div>
            <StatusBadge status={infra.overall_status} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(infra.services).map(([name, status]) => (
              <div key={name} className="rounded-md border border-apex-line bg-white/[0.03] p-3">
                <div className="text-xs uppercase tracking-[0.16em] text-apex-muted">{name}</div>
                <div className="mt-2"><StatusBadge status={status} /></div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {loading ? <div className="panel p-5 text-apex-muted">Carregando projetos...</div> : null}
      <ProjectSelector projects={projects} selectedId={selectedId} onChange={setSelectedId} />
      <div className="panel p-4">
        <div className="mb-3 flex items-center gap-2 text-white">
          <Activity className="h-5 w-5 text-apex-cyan" />
          Container
        </div>
        <pre className="max-h-96 overflow-auto rounded-md border border-apex-line bg-black/40 p-3 text-xs text-apex-muted">
          {projectMetric ? JSON.stringify(projectMetric, null, 2) : "Selecione um projeto."}
        </pre>
      </div>
    </div>
  );
}
