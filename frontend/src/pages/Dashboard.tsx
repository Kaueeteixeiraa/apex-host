import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Boxes,
  Cpu,
  Database,
  DatabaseBackup,
  Globe2,
  HardDrive,
  Network,
  type LucideIcon,
  MemoryStick,
  Rocket,
  Settings,
  ShieldAlert,
  ShieldCheck
} from "lucide-react";
import { Link } from "react-router-dom";

import { api, BackupRecord, DashboardStats, Deploy, formatDate, InfrastructureStatus, ProductionAudit, Project } from "../lib/api";
import { DashboardSkeleton } from "../components/Skeleton";
import { EmptyState } from "../components/EmptyState";
import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
import { ProjectCard } from "../components/ProjectCard";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";

export function Dashboard() {
  const [data, setData] = useState<DashboardStats | null>(null);
  const [infra, setInfra] = useState<InfrastructureStatus | null>(null);
  const [audit, setAudit] = useState<ProductionAudit | null>(null);
  const [backups, setBackups] = useState<BackupRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = async () => {
    const [dashboard, infraStatus, backupList, auditData] = await Promise.all([
      api<DashboardStats>("/dashboard"),
      api<InfrastructureStatus>("/monitor/infrastructure"),
      api<BackupRecord[]>("/backups").catch(() => []),
      api<ProductionAudit>("/production-audit").catch(() => null)
    ]);
    setData(dashboard);
    setInfra(infraStatus);
    setBackups(backupList);
    setAudit(auditData);
  };

  useEffect(() => {
    void load().catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar dashboard"));
  }, []);

  const quickDeploy = async (project: Project) => {
    setMessage(null);
    const deploy = await api<Deploy>(`/projects/${project.id}/deploys`, {
      method: "POST",
      body: JSON.stringify({})
    });
    setMessage(`Deploy #${deploy.id} enfileirado para ${project.name}.`);
    await load();
  };

  if (error) return <FeedbackBanner type="error" message={error} />;
  if (!data) return <DashboardSkeleton />;

  const health = data.error_projects > 0 ? "Atencao necessaria" : data.building_projects > 0 ? "Deploys em andamento" : "Operacao estavel";

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Infraestrutura privada Apex"
        title="Dashboard"
        description="Visao operacional de projetos Apex, deploys internos, backups e saude geral da VPS."
        icon={Activity}
      />

      {message ? <FeedbackBanner type="success" message={message} /> : null}
      {audit?.status === "critical" ? (
        <FeedbackBanner
          type="error"
          message={`Go Live inseguro: ${audit.critical_failures.slice(0, 4).join(", ")}${audit.critical_failures.length > 4 ? "..." : ""}. Abra Auditoria de Producao antes de liberar colaboradores.`}
        />
      ) : null}

      <section className="panel relative overflow-hidden p-5">
        <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-apex-cyan/10 blur-3xl" />
        <div className="relative grid gap-5 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div>
            <div className="section-title">Status da plataforma</div>
            <h2 className="mt-2 text-3xl font-semibold text-white">{health}</h2>
            <p className="muted mt-2 max-w-2xl">
              {data.online_projects} projetos online, {data.offline_projects} offline e {data.error_projects} com erro. O painel indica claramente quando o modo seguro
              esta em dry run.
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
        <StatCard title="Projetos online" value={data.online_projects} icon={Boxes} detail="Sites respondendo" />
        <StatCard title="Projetos offline" value={data.offline_projects + data.error_projects} icon={AlertTriangle} detail="Exigem verificacao" />
        <StatCard title="Ultimo deploy" value={data.recent_deploys[0] ? `#${data.recent_deploys[0].id}` : "-"} icon={Rocket} detail={data.recent_deploys[0] ? formatDate(data.recent_deploys[0].started_at) : "Nenhum deploy"} />
        <StatCard title="Ultimo backup" value={backups[0] ? `#${backups[0].id}` : "-"} icon={DatabaseBackup} detail={backups[0] ? formatDate(backups[0].created_at) : "Nenhum backup"} />
        <StatCard title="Worker" value={infra?.services.worker || "unknown"} icon={Activity} detail="Fila de deploys" />
        <StatCard title="Banco" value={infra?.services.postgres || "unknown"} icon={Database} detail="Persistencia principal" />
        <StatCard title="Redis" value={infra?.services.redis || "unknown"} icon={Network} detail="Fila/cache" />
        <StatCard title="Nginx" value={infra?.services.nginx || "unknown"} icon={Globe2} detail="Proxy local" />
        <StatCard title="Disco livre" value={`${data.server.disk_free_gb ?? Math.max(data.server.disk_total_gb - data.server.disk_used_gb, 0).toFixed(1)} GB`} icon={HardDrive} detail={`${data.server.disk_percent}% usado`} />
        <StatCard title="SSL proximo" value="0" icon={ShieldCheck} detail="Sem certificados vencendo registrados" />
      </section>

      <section className="grid gap-4 lg:grid-cols-4">
        <GoLiveCard
          icon={Rocket}
          title="Go Live"
          detail="Publicar Apex Host em dominio real"
          action="Checklist"
          to="/production-audit"
        />
        <GoLiveCard
          icon={ShieldAlert}
          title="Auditoria de Producao"
          detail={audit ? `${audit.score}% pronto` : "Carregar auditoria"}
          action="Abrir auditoria"
          to="/production-audit"
        />
        <GoLiveCard
          icon={Globe2}
          title="Primeiro deploy publico"
          detail="Docker, Nginx, SSL e health check reais"
          action="Novo projeto"
          to="/projects/new?template=apex-realms"
        />
        <GoLiveCard
          icon={Boxes}
          title="Apex Realms"
          detail="Projeto interno recomendado"
          action="Publicar Apex Realms"
          to="/projects/new?template=apex-realms"
        />
      </section>

      {infra?.dry_run ? (
        <section className="panel border-yellow-400/30 bg-yellow-400/5 p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="text-sm font-semibold text-yellow-100">DRY RUN ATIVO</div>
              <p className="muted mt-1">Deploys reais com Docker estao desativados neste ambiente. Use o modo producao somente na VPS preparada.</p>
            </div>
            <Link className="btn-secondary" to="/help">
              Como ativar producao
            </Link>
          </div>
        </section>
      ) : null}

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
            title="Nenhum projeto hospedado ainda"
            description="A infraestrutura esta pronta para receber o primeiro site interno da Apex."
            action={
              <div className="flex flex-wrap justify-center gap-2">
                <Link className="btn-primary" to="/projects/new?template=apex-realms">
                  <Rocket className="h-4 w-4" />
                  Publicar Apex Realms
                </Link>
                <Link className="btn-secondary" to="/projects/new">
                  Criar projeto manualmente
                </Link>
              </div>
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

function GoLiveCard({ icon: Icon, title, detail, action, to }: { icon: LucideIcon; title: string; detail: string; action: string; to: string }) {
  return (
    <Link className="panel block p-4 hover:-translate-y-0.5 hover:border-apex-cyan/60" to={to}>
      <div className="mb-4 flex items-center justify-between">
        <Icon className="h-5 w-5 text-apex-cyan" />
        <span className="rounded-full border border-apex-cyan/30 bg-apex-cyan/10 px-2 py-0.5 text-xs text-apex-cyan">Go Live</span>
      </div>
      <h2 className="font-semibold text-white">{title}</h2>
      <p className="muted mt-1 min-h-10">{detail}</p>
      <div className="mt-4 text-sm font-medium text-apex-cyan">{action}</div>
    </Link>
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
