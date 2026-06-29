import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Github, Plus, RefreshCcw, Trash2 } from "lucide-react";

import { api, formatDate, GitHubRepo, Project } from "../lib/api";
import { StatusBadge } from "../components/StatusBadge";

const emptyForm = {
  name: "",
  slug: "",
  github_url: "",
  branch: "main",
  project_type: "manual",
  install_command: "",
  build_command: "",
  start_command: "",
  internal_port: 3000
};

export function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setProjects(await api<Project[]>("/projects"));
  };

  useEffect(() => {
    void load().catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar projetos"));
    void api<GitHubRepo[]>("/github/repos").then(setRepos).catch(() => setRepos([]));
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api<Project>("/projects", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          slug: form.slug || null,
          github_url: form.github_url || null,
          install_command: form.install_command || null,
          build_command: form.build_command || null,
          start_command: form.start_command || null,
          github_repo_full_name: repos.find((repo) => repo.clone_url === form.github_url)?.full_name || null
        })
      });
      setForm(emptyForm);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar projeto");
    } finally {
      setLoading(false);
    }
  };

  const remove = async (id: number) => {
    if (!confirm("Excluir este projeto?")) return;
    await api(`/projects/${id}`, { method: "DELETE" });
    await load();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Projetos</h1>
        <p className="muted mt-1">Cadastre repositorios, comandos e portas para preparar deploys.</p>
      </div>

      <form className="panel grid gap-4 p-4 lg:grid-cols-4" onSubmit={submit}>
        <div className="lg:col-span-2">
          <label className="label">Nome</label>
          <input className="field" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
        </div>
        <div>
          <label className="label">Slug</label>
          <input className="field" value={form.slug} onChange={(event) => setForm({ ...form, slug: event.target.value })} placeholder="auto" />
        </div>
        <div>
          <label className="label">Branch</label>
          <input className="field" value={form.branch} onChange={(event) => setForm({ ...form, branch: event.target.value })} />
        </div>
        <div className="lg:col-span-2">
          <label className="label">Repositorio GitHub</label>
          <input
            className="field"
            value={form.github_url}
            onChange={(event) => setForm({ ...form, github_url: event.target.value })}
            placeholder="https://github.com/org/repo.git"
          />
        </div>
        {repos.length > 0 ? (
          <div className="lg:col-span-2">
            <label className="label">Repositorios conectados</label>
            <select
              className="field"
              onChange={(event) => {
                const repo = repos.find((item) => item.full_name === event.target.value);
                if (repo) setForm({ ...form, github_url: repo.clone_url, branch: repo.default_branch });
              }}
              defaultValue=""
            >
              <option value="">Selecionar do GitHub</option>
              {repos.map((repo) => (
                <option key={repo.full_name} value={repo.full_name}>
                  {repo.full_name}
                </option>
              ))}
            </select>
          </div>
        ) : null}
        <div>
          <label className="label">Tipo</label>
          <select className="field" value={form.project_type} onChange={(event) => setForm({ ...form, project_type: event.target.value })}>
            <option value="manual">manual</option>
            <option value="react-vite">react-vite</option>
            <option value="nextjs">nextjs</option>
            <option value="node">node</option>
            <option value="fastapi">fastapi</option>
            <option value="flask">flask</option>
            <option value="static">static</option>
          </select>
        </div>
        <div>
          <label className="label">Porta interna</label>
          <input
            className="field"
            type="number"
            value={form.internal_port}
            onChange={(event) => setForm({ ...form, internal_port: Number(event.target.value) })}
          />
        </div>
        <div>
          <label className="label">Install</label>
          <input className="field" value={form.install_command} onChange={(event) => setForm({ ...form, install_command: event.target.value })} />
        </div>
        <div>
          <label className="label">Build</label>
          <input className="field" value={form.build_command} onChange={(event) => setForm({ ...form, build_command: event.target.value })} />
        </div>
        <div>
          <label className="label">Start</label>
          <input className="field" value={form.start_command} onChange={(event) => setForm({ ...form, start_command: event.target.value })} />
        </div>
        <div className="flex items-end">
          <button className="btn-primary w-full" disabled={loading}>
            <Plus className="h-4 w-4" />
            Criar
          </button>
        </div>
      </form>
      {error ? <div className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{error}</div> : null}

      <div className="panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-apex-line p-4">
          <h2 className="font-semibold text-white">Projetos cadastrados</h2>
          <button className="btn-secondary" onClick={() => void load()}>
            <RefreshCcw className="h-4 w-4" />
            Atualizar
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="text-xs uppercase tracking-[0.12em] text-apex-muted">
              <tr className="border-b border-apex-line">
                <th className="p-4">Projeto</th>
                <th className="p-4">Status</th>
                <th className="p-4">Tipo</th>
                <th className="p-4">Dominio</th>
                <th className="p-4">Ultimo deploy</th>
                <th className="p-4" />
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id} className="border-b border-apex-line/70">
                  <td className="p-4">
                    <Link className="font-medium text-white hover:text-apex-cyan" to={`/projects/${project.id}`}>
                      {project.name}
                    </Link>
                    <div className="flex items-center gap-1 text-xs text-apex-muted">
                      <Github className="h-3 w-3" />
                      {project.github_repo_full_name || project.github_url || "Repositorio nao configurado"}
                    </div>
                  </td>
                  <td className="p-4">
                    <StatusBadge status={project.status} />
                  </td>
                  <td className="p-4 text-apex-muted">{project.project_type}</td>
                  <td className="p-4 text-apex-muted">{project.primary_domain || project.auto_subdomain}</td>
                  <td className="p-4 text-apex-muted">{formatDate(project.last_deploy_at)}</td>
                  <td className="p-4 text-right">
                    <button className="btn-danger" onClick={() => void remove(project.id)}>
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {projects.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-apex-muted">
                    Nenhum projeto ainda.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
