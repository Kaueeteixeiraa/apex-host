import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Search, RefreshCcw, ScrollText, Trash2 } from "lucide-react";

import { api, formatDate, LogEntry } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { ProjectSelector } from "../components/ProjectSelector";
import { ProjectTabs } from "../components/ProjectTabs";
import { useProjectScope } from "../lib/useProjectScope";

export function Logs() {
  const { projectId } = useParams();
  const { projects, selectedId, selectedProject, setSelectedId, loading, error } = useProjectScope(projectId);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [type, setType] = useState("");
  const [query, setQuery] = useState("");
  const [autoPoll, setAutoPoll] = useState(true);

  const loadLogs = async () => {
    if (!selectedId) return;
    const suffix = type ? `?type=${encodeURIComponent(type)}` : "";
    setLogs(await api<LogEntry[]>(`/projects/${selectedId}/logs${suffix}`));
  };

  useEffect(() => {
    void loadLogs();
    if (!autoPoll) return;
    const interval = window.setInterval(() => void loadLogs(), 5000);
    return () => window.clearInterval(interval);
  }, [selectedId, type, autoPoll]);

  const filteredLogs = useMemo(() => {
    const search = query.toLowerCase().trim();
    if (!search) return logs;
    return logs.filter((log) => `${log.type} ${log.message} ${log.created_at}`.toLowerCase().includes(search));
  }, [logs, query]);

  if (error) return <div className="panel p-5 text-red-200">{error}</div>;

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Observability"
        title="Logs"
        description="Build, runtime, erros e eventos de auditoria operacional em uma visao de terminal."
        icon={ScrollText}
      />
      {selectedProject ? <ProjectTabs projectId={selectedProject.id} /> : null}
      {loading ? <div className="panel p-5 text-apex-muted">Carregando projetos...</div> : null}
      <div className="panel grid gap-4 p-4 lg:grid-cols-[1fr_180px_1fr_auto_auto] lg:items-end">
        <ProjectSelector projects={projects} selectedId={selectedId} onChange={setSelectedId} />
        <label className="block">
          <span className="label">Tipo</span>
          <select className="field" value={type} onChange={(event) => setType(event.target.value)}>
            <option value="">todos</option>
            <option value="deploy">deploy</option>
            <option value="system">system</option>
            <option value="error">error</option>
            <option value="app">app</option>
            <option value="ssl">ssl</option>
          </select>
        </label>
        <label className="block">
          <span className="label">Busca</span>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-apex-muted" />
            <input className="field pl-9" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="erro, build, deploy..." />
          </div>
        </label>
        <label className="flex items-center gap-2 pb-2 text-sm text-apex-muted">
          <input type="checkbox" checked={autoPoll} onChange={(event) => setAutoPoll(event.target.checked)} />
          Auto
        </label>
        <button className="btn-secondary" onClick={() => void loadLogs()}>
          <RefreshCcw className="h-4 w-4" />
          Atualizar
        </button>
        <button className="btn-secondary lg:col-start-5" onClick={() => setLogs([])}>
          <Trash2 className="h-4 w-4" />
          Limpar tela
        </button>
      </div>
      <div className="terminal max-h-[680px] overflow-auto p-0">
        {filteredLogs.map((log) => (
          <div key={log.id} className="border-b border-apex-line/70 p-4">
            <div className="flex flex-wrap items-center gap-2 text-xs text-apex-muted">
              <span className="rounded-full border border-apex-cyan/30 bg-apex-cyan/10 px-2 py-1 text-apex-cyan">{log.type}</span>
              <span>{formatDate(log.created_at)}</span>
              {log.deploy_id ? <span>deploy #{log.deploy_id}</span> : null}
            </div>
            <div className="mt-2 whitespace-pre-wrap text-sm">{log.message}</div>
          </div>
        ))}
        {filteredLogs.length === 0 ? <div className="p-5 text-apex-muted">Nenhum log encontrado.</div> : null}
      </div>
    </div>
  );
}
