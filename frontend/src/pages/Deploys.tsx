import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { History, Play, RefreshCcw, RotateCcw, ShieldCheck, Sparkles, XCircle } from "lucide-react";

import { Deploy, LogAnalysis, api, formatDate } from "../lib/api";
import { EmptyState } from "../components/EmptyState";
import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
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
  const [analysis, setAnalysis] = useState<Record<number, LogAnalysis>>({});

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

  const rollback = async (deployId: number) => {
    if (!selectedId) return;
    const deploy = await api<Deploy>(`/projects/${selectedId}/deploys/rollback`, {
      method: "POST",
      body: JSON.stringify({ dry_run: true, target_deploy_id: deployId })
    });
    setMessage(`Rollback dry run #${deploy.id} enfileirado.`);
    await loadDeploys();
  };

  const analyzeDeploy = async (deployId: number) => {
    if (!selectedId) return;
    const result = await api<LogAnalysis>(`/projects/${selectedId}/deploys/${deployId}/analysis`, { method: "POST" });
    setAnalysis({ ...analysis, [deployId]: result });
  };

  if (error) return <div className="panel p-5 text-red-200">{error}</div>;

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Release Pipeline"
        title="Deploys"
        description="Execute deploy manual, acompanhe etapas, cancele jobs e prepare rollback seguro."
        icon={History}
      />
      {selectedProject ? <ProjectTabs projectId={selectedProject.id} /> : null}
      {loading ? <div className="panel p-5 text-apex-muted">Carregando projetos...</div> : null}
      <ProjectSelector projects={projects} selectedId={selectedId} onChange={setSelectedId} />

      {selectedId ? (
        <>
          <div className="panel flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <label className="flex items-center gap-2 text-sm text-apex-muted">
                <input type="checkbox" checked={dryRun} onChange={(event) => setDryRun(event.target.checked)} />
                Dry run: clona e registra etapas sem alterar containers
              </label>
              <div className="mt-2 flex items-center gap-2 text-xs text-apex-muted">
                <ShieldCheck className="h-3.5 w-3.5 text-apex-cyan" />
                Validacao de comandos e auditoria ativa.
              </div>
            </div>
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
          {message ? <FeedbackBanner type="success" message={message} /> : null}
          <div className="space-y-3">
            {deploys.map((deploy) => (
              <div key={deploy.id} className="panel overflow-hidden p-4">
                <div className="mb-4 grid grid-cols-4 gap-1">
                  {["queued", "running", "success", "failed"].map((status) => (
                    <div
                      key={status}
                      className={`h-1 rounded-full ${
                        deploy.status === status || (status === "success" && deploy.status === "success") ? "bg-apex-cyan shadow-glow" : "bg-white/10"
                      }`}
                    />
                  ))}
                </div>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="font-semibold text-white">Deploy #{deploy.id}</h2>
                      <StatusBadge status={deploy.status} />
                    </div>
                    <p className="muted mt-1">
                      Branch {deploy.branch} - {formatDate(deploy.started_at)} - {deploy.dry_run ? "dry run" : "docker"} - {deploy.deploy_type}
                    </p>
                    {deploy.commit_sha ? <p className="mt-1 text-xs text-apex-muted">Commit {deploy.commit_sha.slice(0, 12)}</p> : null}
                    {deploy.commit_author || deploy.commit_message ? (
                      <p className="mt-1 text-xs text-apex-muted">
                        {deploy.commit_author || "Autor desconhecido"} - {deploy.commit_message || "Sem mensagem"}
                      </p>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {deploy.status === "success" && deploy.commit_sha ? (
                      <button className="btn-secondary" onClick={() => void rollback(deploy.id)}>
                        <RotateCcw className="h-4 w-4" />
                        Rollback
                      </button>
                    ) : null}
                    {(deploy.status === "failed" || deploy.error || deploy.logs) ? (
                      <button className="btn-secondary" onClick={() => void analyzeDeploy(deploy.id)}>
                        <Sparkles className="h-4 w-4" />
                        Analisar erro
                      </button>
                    ) : null}
                    {deploy.status === "queued" || deploy.status === "running" ? (
                      <button className="btn-danger" onClick={() => void cancel(deploy.id)}>
                        <XCircle className="h-4 w-4" />
                        Cancelar
                      </button>
                    ) : null}
                  </div>
                </div>
                {deploy.error ? <div className="mt-3 rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-100">{deploy.error}</div> : null}
                {analysis[deploy.id] ? (
                  <div className="mt-3 rounded-md border border-apex-cyan/30 bg-apex-cyan/10 p-3 text-sm text-apex-text">
                    <div className="font-medium text-white">{analysis[deploy.id].possible_cause}</div>
                    <p className="mt-1 text-apex-muted">{analysis[deploy.id].suggested_fix}</p>
                  </div>
                ) : null}
                {deploy.logs ? (
                  <pre className="terminal mt-3 max-h-80 overflow-auto p-3">
                    {deploy.logs}
                  </pre>
                ) : null}
              </div>
            ))}
            {deploys.length === 0 ? (
              <EmptyState
                icon={History}
                title="Nenhum deploy para este projeto"
                description="Execute o primeiro deploy em dry run para validar comandos, logs e auditoria."
                action={
                  <button className="btn-primary" onClick={() => void trigger()}>
                    <Play className="h-4 w-4" />
                    Novo deploy
                  </button>
                }
              />
            ) : null}
          </div>
        </>
      ) : (
        <EmptyState icon={History} title="Selecione um projeto" description="Escolha um projeto hospedado para acompanhar deploys e preparar rollback." />
      )}
    </div>
  );
}
