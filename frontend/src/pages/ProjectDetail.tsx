import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ExternalLink, GitBranch, Pause, Play, RotateCcw, Rocket, Save, Square, TerminalSquare } from "lucide-react";

import { api, Deploy, formatDate, Project } from "../lib/api";
import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
import { ProjectTabs } from "../components/ProjectTabs";
import { StatusBadge } from "../components/StatusBadge";

export function ProjectDetail() {
  const { projectId } = useParams();
  const [project, setProject] = useState<Project | null>(null);
  const [form, setForm] = useState<Partial<Project>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    const item = await api<Project>(`/projects/${projectId}`);
    setProject(item);
    setForm(item);
  };

  useEffect(() => {
    void load().catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar projeto"));
  }, [projectId]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setMessage(null);
    setError(null);
    try {
      const updated = await api<Project>(`/projects/${projectId}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: form.name,
          slug: form.slug,
          github_url: form.github_url || null,
          branch: form.branch,
          project_type: form.project_type,
          install_command: form.install_command || null,
          build_command: form.build_command || null,
          start_command: form.start_command || null,
          output_directory: form.output_directory || null,
          cpu_limit: form.cpu_limit || null,
          memory_limit: form.memory_limit || null,
          internal_port: form.internal_port,
          primary_domain: form.primary_domain || null
        })
      });
      setProject(updated);
      setForm(updated);
      setMessage("Projeto atualizado.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar projeto");
    }
  };

  const action = async (name: "pause" | "start" | "stop" | "restart") => {
    const updated = await api<Project>(`/projects/${projectId}/${name}`, { method: "POST" });
    setProject(updated);
    setForm(updated);
  };

  const redeploy = async () => {
    const deploy = await api<Deploy>(`/projects/${projectId}/deploys`, {
      method: "POST",
      body: JSON.stringify({})
    });
    setMessage(`Deploy #${deploy.id} enfileirado.`);
  };

  if (error) return <div className="panel p-5 text-red-200">{error}</div>;
  if (!project) return <div className="panel p-5 text-apex-muted">Carregando projeto...</div>;

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Project Overview"
        title={project.name}
        description={project.primary_domain || project.auto_subdomain}
        icon={TerminalSquare}
        actions={
          <>
            <a className="btn-secondary" href={`https://${project.primary_domain || project.auto_subdomain}`} target="_blank" rel="noreferrer">
              <ExternalLink className="h-4 w-4" />
              Abrir site
            </a>
            <button className="btn-primary" onClick={() => void redeploy()}>
              <Rocket className="h-4 w-4" />
              Redeploy
            </button>
          </>
        }
      />
      {message ? <FeedbackBanner type="success" message={message} /> : null}
      <ProjectTabs projectId={project.id} />

      <section className="grid gap-4 md:grid-cols-4">
        <OverviewCard label="Status" value={<StatusBadge status={project.status} />} />
        <OverviewCard label="Branch" value={project.branch} icon={<GitBranch className="h-4 w-4 text-apex-cyan" />} />
        <OverviewCard label="Framework" value={project.project_type} />
        <OverviewCard label="Ultimo deploy" value={formatDate(project.last_deploy_at)} />
      </section>

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <form className="panel grid gap-4 p-4 md:grid-cols-2" onSubmit={submit}>
          <div>
            <label className="label">Nome</label>
            <input className="field" value={form.name || ""} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          </div>
          <div>
            <label className="label">Slug</label>
            <input className="field" value={form.slug || ""} onChange={(event) => setForm({ ...form, slug: event.target.value })} />
          </div>
          <div className="md:col-span-2">
            <label className="label">Repositorio GitHub</label>
            <input className="field" value={form.github_url || ""} onChange={(event) => setForm({ ...form, github_url: event.target.value })} />
          </div>
          <div>
            <label className="label">Branch</label>
            <input className="field" value={form.branch || ""} onChange={(event) => setForm({ ...form, branch: event.target.value })} />
          </div>
          <div>
            <label className="label">Tipo</label>
            <input className="field" value={form.project_type || ""} onChange={(event) => setForm({ ...form, project_type: event.target.value })} />
          </div>
          <div>
            <label className="label">Install</label>
            <input className="field" value={form.install_command || ""} onChange={(event) => setForm({ ...form, install_command: event.target.value })} />
          </div>
          <div>
            <label className="label">Build</label>
            <input className="field" value={form.build_command || ""} onChange={(event) => setForm({ ...form, build_command: event.target.value })} />
          </div>
          <div>
            <label className="label">Start</label>
            <input className="field" value={form.start_command || ""} onChange={(event) => setForm({ ...form, start_command: event.target.value })} />
          </div>
          <div>
            <label className="label">Porta interna</label>
            <input
              className="field"
              type="number"
              value={form.internal_port || 3000}
              onChange={(event) => setForm({ ...form, internal_port: Number(event.target.value) })}
            />
          </div>
          <div>
            <label className="label">Output directory</label>
            <input className="field" value={form.output_directory || ""} onChange={(event) => setForm({ ...form, output_directory: event.target.value })} />
          </div>
          <div>
            <label className="label">CPU max.</label>
            <input className="field" value={form.cpu_limit || ""} onChange={(event) => setForm({ ...form, cpu_limit: event.target.value })} placeholder="0.50" />
          </div>
          <div>
            <label className="label">RAM max.</label>
            <input className="field" value={form.memory_limit || ""} onChange={(event) => setForm({ ...form, memory_limit: event.target.value })} placeholder="512m" />
          </div>
          <div className="md:col-span-2">
            <label className="label">Dominio principal</label>
            <input className="field" value={form.primary_domain || ""} onChange={(event) => setForm({ ...form, primary_domain: event.target.value })} />
          </div>
          <div className="md:col-span-2">
            <button className="btn-primary">
              <Save className="h-4 w-4" />
              Salvar alteracoes
            </button>
          </div>
        </form>

        <aside className="panel h-fit space-y-3 p-4">
          <h2 className="font-semibold text-white">Acoes</h2>
          <button className="btn-secondary w-full" onClick={() => void action("start")}>
            <Play className="h-4 w-4" />
            Iniciar
          </button>
          <button className="btn-secondary w-full" onClick={() => void action("restart")}>
            <RotateCcw className="h-4 w-4" />
            Reiniciar
          </button>
          <button className="btn-secondary w-full" onClick={() => void action("pause")}>
            <Pause className="h-4 w-4" />
            Pausar
          </button>
          <button className="btn-secondary w-full" onClick={() => void action("stop")}>
            <Square className="h-4 w-4" />
            Parar
          </button>
          <div className="rounded-md border border-apex-line p-3 text-xs text-apex-muted">
            Host port: {project.host_port || "sera alocada no deploy Docker"}
          </div>
        </aside>
      </div>
    </div>
  );
}

function OverviewCard({ label, value, icon }: { label: string; value: string | JSX.Element; icon?: JSX.Element }) {
  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between">
        <div className="text-xs uppercase tracking-[0.12em] text-apex-muted">{label}</div>
        {icon}
      </div>
      <div className="mt-3 text-sm font-medium text-white">{value}</div>
    </div>
  );
}
