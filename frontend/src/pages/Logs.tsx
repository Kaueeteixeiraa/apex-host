import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Copy, Download, Search, RefreshCcw, ScrollText, Sparkles, Trash2 } from "lucide-react";

import { api, formatDate, LogAnalysis, LogEntry } from "../lib/api";
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
  const [analysis, setAnalysis] = useState<LogAnalysis | null>(null);

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

  const analyze = async () => {
    if (!selectedId) return;
    setAnalysis(await api<LogAnalysis>(`/projects/${selectedId}/logs/analyze`, { method: "POST", body: JSON.stringify({ limit: 300 }) }));
  };

  const formatLogLines = () => filteredLogs.map((log) => `[${formatDate(log.created_at)}] ${log.type}: ${log.message}`).join("\n");

  const copyLogs = async () => {
    await navigator.clipboard.writeText(formatLogLines());
  };

  const downloadLogs = () => {
    const blob = new Blob([formatLogLines()], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `apex-host-logs-${selectedProject?.slug || selectedId || "geral"}.txt`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

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
      <div className="panel grid gap-4 p-4 lg:grid-cols-[1fr_160px_1fr_auto_auto_auto_auto_auto] lg:items-end">
        <ProjectSelector projects={projects} selectedId={selectedId} onChange={setSelectedId} />
        <label className="block">
          <span className="label">Tipo</span>
          <select className="field" value={type} onChange={(event) => setType(event.target.value)}>
            <option value="">todos</option>
            <option value="deploy">deploy</option>
            <option value="build">build</option>
            <option value="runtime">runtime</option>
            <option value="api">api</option>
            <option value="worker">worker</option>
            <option value="system">system</option>
            <option value="error">error</option>
            <option value="warning">warning</option>
            <option value="success">success</option>
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
        <button className="btn-primary" onClick={() => void analyze()}>
          <Sparkles className="h-4 w-4" />
          Analisar erro
        </button>
        <button className="btn-secondary" onClick={() => void copyLogs()} disabled={filteredLogs.length === 0}>
          <Copy className="h-4 w-4" />
          Copiar
        </button>
        <button className="btn-secondary" onClick={downloadLogs} disabled={filteredLogs.length === 0}>
          <Download className="h-4 w-4" />
          Baixar
        </button>
        <button className="btn-secondary" onClick={() => setLogs([])}>
          <Trash2 className="h-4 w-4" />
          Limpar tela
        </button>
      </div>
      {analysis ? (
        <div className="panel grid gap-4 p-4 lg:grid-cols-[1fr_1fr]">
          <div>
            <div className="section-title mb-2">Analise inteligente</div>
            <h2 className="font-semibold text-white">{analysis.possible_cause}</h2>
            <p className="muted mt-2">{analysis.summary}</p>
            <div className="mt-3 rounded-md border border-apex-cyan/30 bg-apex-cyan/10 p-3 text-sm text-apex-text">{analysis.suggested_fix}</div>
          </div>
          <div>
            <div className="section-title mb-2">Linhas importantes</div>
            <div className="terminal max-h-48 overflow-auto p-3">
              {analysis.important_lines.length > 0 ? analysis.important_lines.map((line, index) => <div key={`${line}-${index}`}>{line}</div>) : "Nenhuma linha critica detectada."}
            </div>
          </div>
        </div>
      ) : null}
      <div className="terminal max-h-[680px] overflow-auto p-0">
        {filteredLogs.map((log) => (
          <div key={log.id} className={`border-b border-l-2 border-b-apex-line/70 p-4 ${logTone(log.type)}`}>
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

function logTone(type: string) {
  if (type === "error") return "border-l-red-400 bg-red-500/5";
  if (type === "warning") return "border-l-yellow-300 bg-yellow-500/5";
  if (type === "success") return "border-l-emerald-300 bg-emerald-500/5";
  if (type === "deploy" || type === "build") return "border-l-apex-cyan bg-apex-cyan/5";
  return "border-l-white/10";
}
