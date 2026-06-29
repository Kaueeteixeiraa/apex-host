import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Pause, Play, RotateCcw, Save, Square } from "lucide-react";

import { api, Project } from "../lib/api";
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

  if (error) return <div className="panel p-5 text-red-200">{error}</div>;
  if (!project) return <div className="panel p-5 text-apex-muted">Carregando projeto...</div>;

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="page-title">{project.name}</h1>
          <p className="muted mt-1">{project.primary_domain || project.auto_subdomain}</p>
        </div>
        <StatusBadge status={project.status} />
      </div>
      <ProjectTabs projectId={project.id} />

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
          <div className="md:col-span-2">
            <label className="label">Dominio principal</label>
            <input className="field" value={form.primary_domain || ""} onChange={(event) => setForm({ ...form, primary_domain: event.target.value })} />
          </div>
          {message ? <div className="rounded-md border border-emerald-500/40 bg-emerald-500/10 p-3 text-sm text-emerald-200 md:col-span-2">{message}</div> : null}
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
