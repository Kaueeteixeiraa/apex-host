import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Boxes,
  Cpu,
  Globe2,
  HardDrive,
  type LucideIcon,
  MemoryStick,
  Rocket,
  ScrollText,
  Settings
} from "lucide-react";
import { Link } from "react-router-dom";

import { api, DashboardStats, Deploy, formatDate, Project } from "../lib/api";
import { DashboardSkeleton } from "../components/Skeleton";
import { EmptyState } from "../components/EmptyState";
import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
import { ProjectCard } from "../components/ProjectCard";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";

export function Dashboard() {
  const [data, setData] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = async () => {
    setData(await api<DashboardStats>("/dashboard"));
  };

  useEffect(() => {
    void load().catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar dashboard"));
  }, []);

  const quickDeploy = async (project: Project) => {
    setMessage(null);
    const deploy = await api<Deploy>(`/projects/${project.id}/deploys`, {
      method: "POST",
      body: JSON.stringify({ dry_run: true })
    });
    setMessage(`Deploy dry run #${deploy.id} enfileirado para ${project.name}.`);
    await load();
  };

  if (error) return <FeedbackBanner type="error" message={error} />;
  if (!data) return <DashboardSkeleton />;

  const health = data.error_projects > 0 ? "Atencao necessaria" : data.building_projects > 0 ? "Deploys em andamento" : "Operacao estavel";

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Apex Host Control Plane"
        title="Dashboard"
        description="Visao operacional dos projetos, deploys, dominios e saude geral da VPS."
        icon={Activity}
        actions={
          <>
            <Link to="/logs" className="btn-secondary">
              <ScrollText className="h-4 w-4" />
              Logs
            </Link>
            <Link to="/projects" className="btn-primary">
              <Rocket className="h-4 w-4" />
              Novo projeto
            </Link>
          </>
        }
      />

      {message ? <FeedbackBanner type="success" message={message} /> : null}

      <section className="panel relative overflow-hidden p-5">
        <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-apex-cyan/10 blur-3xl" />
        <div className="relative grid gap-5 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div>
            <div className="section-title">Status da plataforma</div>
            <h2 className="mt-2 text-3xl font-semibold text-white">{health}</h2>
            <p className="muted mt-2 max-w-2xl">
              {data.online_projects} projetos online, {data.building_projects} buildando e {data.error_projects} com erro. O modo seguro deixa deploys em dry run
              ate voce ativar Docker em producao.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <MetricBar label="CPU" value={data.server.cpu_percent} detail="uso atual" />
            <MetricBar label="RAM" value={data.server.memory_percent} detail={`${data.server.memory_used_gb}/${data.server.memory_total_gb} GB`} />
            <MetricBar label="Disco" value={data.server.disk_percent} detail={`${data.server.disk_used_gb}/${data.server.disk_total_gb} GB`} />
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Total de projetos" value={data.total_projects} icon={Boxes} detail={`${data.online_projects} online`} />
        <StatCard title="Dominios ativos" value={data.active_domains} icon={Globe2} detail="Custom + subdominios" />
        <StatCard title="Deploys com erro" value={data.error_projects} icon={AlertTriangle} detail="Projetos em estado de erro" />
        <StatCard title="CPU do servidor" value={`${data.server.cpu_percent}%`} icon={Cpu} detail="Leitura instantanea" />
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold text-white">Projetos recentes</h2>
          <Link className="text-sm text-apex-cyan hover:text-white" to="/projects">
            Ver todos
          </Link>
        </div>
        {data.recent_projects.length > 0 ? (
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {data.recent_projects.map((project) => (
              <ProjectCard key={project.id} project={project} onDeploy={(item) => void quickDeploy(item)} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Boxes}
            title="Nenhum projeto ainda"
            description="Crie o primeiro projeto para conectar repositorio, configurar dominio e iniciar deploys controlados."
            action={
              <Link className="btn-primary" to="/projects">
                <Rocket className="h-4 w-4" />
                Criar projeto
              </Link>
            }
          />
        )}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <ActivityPanel icon={MemoryStick} title="RAM" value={`${data.server.memory_percent}%`} detail={`${data.server.memory_used_gb} GB em uso`} />
        <ActivityPanel icon={HardDrive} title="Storage" value={`${data.server.disk_percent}%`} detail={`${data.server.disk_used_gb} GB ocupados`} />
        <div className="panel p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-white">Atalhos</h2>
            <Settings className="h-5 w-5 text-apex-cyan" />
          </div>
          <div className="grid gap-2">
            <Link className="btn-secondary justify-start" to="/deploys">
              <Rocket className="h-4 w-4" />
              Central de deploys
            </Link>
            <Link className="btn-secondary justify-start" to="/domains">
              <Globe2 className="h-4 w-4" />
              Dominios
            </Link>
            <Link className="btn-secondary justify-start" to="/settings">
              <Settings className="h-4 w-4" />
              Configuracoes
            </Link>
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

function MetricBar({ label, value, detail }: { label: string; value: number; detail: string }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-apex-muted">
        <span>{label}</span>
        <span>{detail}</span>
      </div>
      <div className="h-2 rounded-full bg-white/10">
        <div className="h-2 rounded-full bg-apex-cyan shadow-glow transition-all" style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
    </div>
  );
}

function ActivityPanel({
  icon: Icon,
  title,
  value,
  detail
}: {
  icon: LucideIcon;
  title: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="panel p-4">
      <div className="mb-4 flex items-center gap-2 text-white">
        <Icon className="h-5 w-5 text-apex-cyan" />
        {title}
      </div>
      <div className="text-3xl font-semibold text-white">{value}</div>
      <p className="muted mt-2">{detail}</p>
    </div>
  );
}
