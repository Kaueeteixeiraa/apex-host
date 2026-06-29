import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Play, RefreshCcw, XCircle } from "lucide-react";

import { Deploy, api, formatDate } from "../lib/api";
import { ProjectSelector } from "../components/ProjectSelector";
import { ProjectTabs } from "../components/ProjectTabs";
import { StatusBadge } from "../components/StatusBadge";
import { useProjectScope } from "../lib/useProjectScope";

export function Deploys() {
  const { projectId } = useParams();
  const { projects, selectedId, selectedProject, setSelectedId, loading, error } = useProjectScope(projectId);
  const [deploys, setDeploys] = useState<Deploy[]>([]);
  const [dryRun, setDryRun] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

  const loadDeploys = async () => {
    if (!selectedId) return;
    setDeploys(await api<Deploy[]>(`/projects/${selectedId}/deploys`));
  };

  useEffect(() => {
    void loadDeploys();
    const interval = window.setInterval(() => void loadDeploys(), 4000);
    return () => window.clearInterval(interval);
  }, [selectedId]);

  const trigger = async () => {
    if (!selectedId) return;
    setMessage(null);
    const deploy = await api<Deploy>(`/projects/${selectedId}/deploys`, {
      method: "POST",
      body: JSON.stringify({ dry_run: dryRun })
    });
    setMessage(`Deploy #${deploy.id} enfileirado.`);
    await loadDeploys();
  };

  const cancel = async (deployId: number) => {
    if (!selectedId) return;
    await api<Deploy>(`/projects/${selectedId}/deploys/${deployId}/cancel`, { method: "POST" });
    await loadDeploys();
  };

  if (error) return <div className="panel p-5 text-red-200">{error}</div>;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title">Deploys</h1>
        <p className="muted mt-1">Execute deploy manual, acompanhe etapas e historico.</p>
      </div>
      {selectedProject ? <ProjectTabs projectId={selectedProject.id} /> : null}
      {loading ? <div className="panel p-5 text-apex-muted">Carregando projetos...</div> : null}
      <ProjectSelector projects={projects} selectedId={selectedId} onChange={setSelectedId} />

      {selectedId ? (
        <>
          <div className="panel flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
            <label className="flex items-center gap-2 text-sm text-apex-muted">
              <input type="checkbox" checked={dryRun} onChange={(event) => setDryRun(event.target.checked)} />
              Dry run: clona e registra etapas sem alterar containers
            </label>
            <div className="flex gap-2">
              <button className="btn-secondary" onClick={() => void loadDeploys()}>
                <RefreshCcw className="h-4 w-4" />
                Atualizar
              </button>
              <button className="btn-primary" onClick={() => void trigger()}>
                <Play className="h-4 w-4" />
                Novo deploy
              </button>
            </div>
          </div>
          {message ? <div className="rounded-md border border-emerald-500/40 bg-emerald-500/10 p-3 text-sm text-emerald-200">{message}</div> : null}
          <div className="space-y-3">
            {deploys.map((deploy) => (
              <div key={deploy.id} className="panel p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="font-semibold text-white">Deploy #{deploy.id}</h2>
                      <StatusBadge status={deploy.status} />
                    </div>
                    <p className="muted mt-1">
                      Branch {deploy.branch} - {formatDate(deploy.started_at)} - {deploy.dry_run ? "dry run" : "docker"}
                    </p>
                    {deploy.commit_sha ? <p className="mt-1 text-xs text-apex-muted">Commit {deploy.commit_sha.slice(0, 12)}</p> : null}
                  </div>
                  {deploy.status === "queued" || deploy.status === "running" ? (
                    <button className="btn-danger" onClick={() => void cancel(deploy.id)}>
                      <XCircle className="h-4 w-4" />
                      Cancelar
                    </button>
                  ) : null}
                </div>
                {deploy.error ? <div className="mt-3 rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-100">{deploy.error}</div> : null}
                {deploy.logs ? (
                  <pre className="mt-3 max-h-80 overflow-auto rounded-md border border-apex-line bg-black/40 p-3 text-xs text-apex-muted">
                    {deploy.logs}
                  </pre>
                ) : null}
              </div>
            ))}
            {deploys.length === 0 ? <div className="panel p-5 text-apex-muted">Nenhum deploy para este projeto.</div> : null}
          </div>
        </>
      ) : null}
    </div>
  );
}
