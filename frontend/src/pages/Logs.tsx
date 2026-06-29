import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { RefreshCcw } from "lucide-react";

import { api, formatDate, LogEntry } from "../lib/api";
import { ProjectSelector } from "../components/ProjectSelector";
import { ProjectTabs } from "../components/ProjectTabs";
import { useProjectScope } from "../lib/useProjectScope";

export function Logs() {
  const { projectId } = useParams();
  const { projects, selectedId, selectedProject, setSelectedId, loading, error } = useProjectScope(projectId);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [type, setType] = useState("");

  const loadLogs = async () => {
    if (!selectedId) return;
    const suffix = type ? `?type=${encodeURIComponent(type)}` : "";
    setLogs(await api<LogEntry[]>(`/projects/${selectedId}/logs${suffix}`));
  };

  useEffect(() => {
    void loadLogs();
    const interval = window.setInterval(() => void loadLogs(), 5000);
    return () => window.clearInterval(interval);
  }, [selectedId, type]);

  if (error) return <div className="panel p-5 text-red-200">{error}</div>;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title">Logs</h1>
        <p className="muted mt-1">Build, aplicacao, erros e eventos do sistema por projeto.</p>
      </div>
      {selectedProject ? <ProjectTabs projectId={selectedProject.id} /> : null}
      {loading ? <div className="panel p-5 text-apex-muted">Carregando projetos...</div> : null}
      <div className="panel flex flex-col gap-4 p-4 sm:flex-row sm:items-end">
        <ProjectSelector projects={projects} selectedId={selectedId} onChange={setSelectedId} />
        <label className="block">
          <span className="label">Tipo</span>
          <select className="field" value={type} onChange={(event) => setType(event.target.value)}>
            <option value="">todos</option>
            <option value="deploy">deploy</option>
            <option value="system">system</option>
            <option value="error">error</option>
            <option value="app">app</option>
          </select>
        </label>
        <button className="btn-secondary" onClick={() => void loadLogs()}>
          <RefreshCcw className="h-4 w-4" />
          Atualizar
        </button>
      </div>
      <div className="panel overflow-hidden">
        {logs.map((log) => (
          <div key={log.id} className="border-b border-apex-line p-4">
            <div className="flex flex-wrap items-center gap-2 text-xs text-apex-muted">
              <span className="rounded-full border border-apex-line px-2 py-1">{log.type}</span>
              <span>{formatDate(log.created_at)}</span>
              {log.deploy_id ? <span>deploy #{log.deploy_id}</span> : null}
            </div>
            <div className="mt-2 whitespace-pre-wrap text-sm text-apex-text">{log.message}</div>
          </div>
        ))}
        {logs.length === 0 ? <div className="p-5 text-apex-muted">Nenhum log encontrado.</div> : null}
      </div>
    </div>
  );
}
