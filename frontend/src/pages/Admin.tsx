import { useEffect, useState } from "react";
import { AlertTriangle, Boxes, Database, RefreshCcw, Save, Server, Settings2, Shield, Users } from "lucide-react";

import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";
import { AdminOverview, api, formatDate, PlatformSettings, Project, User } from "../lib/api";

export function Admin() {
  const { user } = useAuth();
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [platform, setPlatform] = useState<PlatformSettings | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setOverview(await api<AdminOverview>("/admin/overview"));
    setPlatform(await api<PlatformSettings>("/admin/platform-settings"));
  };

  useEffect(() => {
    if (user?.role === "admin") void load().catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar admin"));
  }, [user?.role]);

  const updateUser = async (item: User, patch: Partial<User>) => {
    await api<User>(`/admin/users/${item.id}`, { method: "PATCH", body: JSON.stringify(patch) });
    setMessage(`Usuario ${item.email} atualizado.`);
    await load();
  };

  const suspendProject = async (project: Project) => {
    await api<Project>(`/admin/projects/${project.id}/suspend`, { method: "POST" });
    setMessage(`Projeto ${project.slug} suspenso.`);
    await load();
  };

  const deleteProject = async (project: Project) => {
    const confirmation = prompt(`Digite ${project.slug} para excluir este projeto`);
    if (confirmation !== project.slug) return;
    await api(`/admin/projects/${project.id}`, { method: "DELETE", body: JSON.stringify({ confirmation }) });
    setMessage(`Projeto ${project.slug} excluido.`);
    await load();
  };

  const savePlatform = async () => {
    if (!platform) return;
    const payload = {
      platform_name: platform.platform_name,
      primary_color: platform.primary_color,
      primary_domain: platform.primary_domain,
      maintenance_mode: platform.maintenance_mode,
      allow_registration: platform.allow_registration,
      require_account_approval: platform.require_account_approval,
      default_user_plan: platform.default_user_plan,
      smtp_config: platform.smtp_config,
      alert_config: platform.alert_config,
      backup_config: platform.backup_config,
      cdn_config: platform.cdn_config
    };
    setPlatform(await api<PlatformSettings>("/admin/platform-settings", { method: "PATCH", body: JSON.stringify(payload) }));
    setMessage("Configuracoes da plataforma salvas.");
  };

  if (user?.role !== "admin") {
    return <FeedbackBanner type="error" message="Acesso restrito a administradores." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Owner Console"
        title="Painel Admin"
        description="Usuarios internos, projetos, nodes, alertas, auditoria, limites e configuracoes globais da infraestrutura."
        icon={Shield}
        actions={
          <button className="btn-secondary" onClick={() => void load()}>
            <RefreshCcw className="h-4 w-4" />
            Atualizar
          </button>
        }
      />
      {message ? <FeedbackBanner type="success" message={message} /> : null}
      {error ? <FeedbackBanner type="error" message={error} /> : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Usuarios" value={overview?.stats.users ?? 0} icon={Users} detail={`${overview?.stats.active_users ?? 0} ativos`} />
        <StatCard title="Projetos" value={overview?.stats.projects ?? 0} icon={Boxes} detail={`${overview?.stats.online_projects ?? 0} online`} />
        <StatCard title="Nodes" value={overview?.stats.nodes ?? 0} icon={Server} detail="VPS/edge cadastrados" />
        <StatCard title="Alertas" value={overview?.stats.open_alerts ?? 0} icon={AlertTriangle} detail="Nao reconhecidos" />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="panel p-4">
          <h2 className="mb-4 flex items-center gap-2 font-semibold text-white">
            <Users className="h-5 w-5 text-apex-cyan" />
            Usuarios cadastrados
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.12em] text-apex-muted">
                <tr>
                  <th className="p-2">Usuario</th>
                  <th className="p-2">Role</th>
                  <th className="p-2">Perfil</th>
                  <th className="p-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {overview?.users.map((item) => (
                  <tr key={item.id} className="border-t border-apex-line">
                    <td className="p-2">
                      <div className="font-medium text-white">{item.full_name}</div>
                      <div className="text-xs text-apex-muted">{item.email}</div>
                    </td>
                    <td className="p-2">
                      <select className="field min-w-28" value={item.role} onChange={(event) => void updateUser(item, { role: event.target.value })}>
                        <option value="admin">admin</option>
                        <option value="dev">dev</option>
                        <option value="viewer">viewer</option>
                      </select>
                    </td>
                    <td className="p-2">
                      <select className="field min-w-32" value={item.plan} onChange={(event) => void updateUser(item, { plan: event.target.value })}>
                        <option value="viewer">viewer</option>
                        <option value="dev">dev</option>
                        <option value="admin_internal">admin_internal</option>
                        <option value="pending_approval">pending_approval</option>
                      </select>
                    </td>
                    <td className="p-2">
                      <button className={item.is_active ? "btn-secondary" : "btn-danger"} onClick={() => void updateUser(item, { is_active: !item.is_active })}>
                        {item.is_active ? "Ativo" : "Bloqueado"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel p-4">
          <h2 className="mb-4 flex items-center gap-2 font-semibold text-white">
            <Settings2 className="h-5 w-5 text-apex-cyan" />
            Configuracoes da plataforma
          </h2>
          {platform ? (
            <div className="space-y-3">
              <label>
                <span className="label">Nome</span>
                <input className="field" value={platform.platform_name} onChange={(event) => setPlatform({ ...platform, platform_name: event.target.value })} />
              </label>
              <div className="grid gap-3 sm:grid-cols-2">
                <label>
                  <span className="label">Cor principal</span>
                  <input className="field" value={platform.primary_color} onChange={(event) => setPlatform({ ...platform, primary_color: event.target.value })} />
                </label>
                <label>
                  <span className="label">Dominio principal</span>
                  <input className="field" value={platform.primary_domain || ""} onChange={(event) => setPlatform({ ...platform, primary_domain: event.target.value || null })} />
                </label>
              </div>
              <div className="grid gap-2 text-sm text-apex-muted">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={platform.maintenance_mode} onChange={(event) => setPlatform({ ...platform, maintenance_mode: event.target.checked })} />
                  Modo manutencao
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={platform.allow_registration} onChange={(event) => setPlatform({ ...platform, allow_registration: event.target.checked })} />
                  Permitir novos cadastros
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={platform.require_account_approval} onChange={(event) => setPlatform({ ...platform, require_account_approval: event.target.checked })} />
                  Exigir aprovacao de conta
                </label>
              </div>
              <label>
                <span className="label">Perfil padrao</span>
                <select className="field" value={platform.default_user_plan} onChange={(event) => setPlatform({ ...platform, default_user_plan: event.target.value })}>
                  <option value="viewer">viewer</option>
                  <option value="dev">dev</option>
                </select>
              </label>
              <button className="btn-primary" onClick={() => void savePlatform()}>
                <Save className="h-4 w-4" />
                Salvar plataforma
              </button>
            </div>
          ) : (
            <p className="muted">Carregando configuracoes...</p>
          )}
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="panel p-4">
          <h2 className="mb-4 flex items-center gap-2 font-semibold text-white">
            <Boxes className="h-5 w-5 text-apex-cyan" />
            Projetos recentes
          </h2>
          <div className="space-y-2">
            {overview?.projects.map((project) => (
              <div key={project.id} className="flex flex-col gap-3 rounded-md border border-apex-line bg-black/20 p-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white">{project.name}</span>
                    <StatusBadge status={project.status} />
                  </div>
                  <div className="text-xs text-apex-muted">{project.slug} - owner #{project.owner_id}</div>
                </div>
                <div className="flex gap-2">
                  <button className="btn-secondary" onClick={() => void suspendProject(project)}>Suspender</button>
                  <button className="btn-danger" onClick={() => void deleteProject(project)}>Excluir</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel p-4">
          <h2 className="mb-4 flex items-center gap-2 font-semibold text-white">
            <Database className="h-5 w-5 text-apex-cyan" />
            Nodes, alertas e auditoria
          </h2>
          <div className="grid gap-3">
            {overview?.nodes.map((node) => (
              <div key={node.id} className="rounded-md border border-apex-line bg-black/20 p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-white">{node.name}</span>
                  <StatusBadge status={node.status} />
                </div>
                <div className="mt-1 text-xs text-apex-muted">{node.role} - {node.cpu_capacity || "CPU n/a"} - {node.ram_capacity || "RAM n/a"}</div>
              </div>
            ))}
            {overview?.alerts.slice(0, 4).map((alert) => (
              <div key={alert.id} className="rounded-md border border-yellow-400/30 bg-yellow-400/10 p-3 text-sm text-yellow-50">
                {alert.message}
                <div className="mt-1 text-xs text-yellow-100/70">{formatDate(alert.created_at)}</div>
              </div>
            ))}
            {overview?.audit_logs.slice(0, 5).map((entry) => (
              <div key={entry.id} className="rounded-md border border-apex-line bg-black/20 p-3 text-sm">
                <span className="text-white">{entry.action}</span>
                <span className="ml-2 text-xs text-apex-muted">{formatDate(entry.created_at)}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
