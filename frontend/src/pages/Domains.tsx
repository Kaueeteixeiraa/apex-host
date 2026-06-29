import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { CheckCircle2, Plus, RefreshCcw, Trash2 } from "lucide-react";

import { api, Domain } from "../lib/api";
import { ProjectSelector } from "../components/ProjectSelector";
import { ProjectTabs } from "../components/ProjectTabs";
import { useProjectScope } from "../lib/useProjectScope";

export function Domains() {
  const { projectId } = useParams();
  const { projects, selectedId, selectedProject, setSelectedId, loading, error } = useProjectScope(projectId);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [hostname, setHostname] = useState("");
  const [primary, setPrimary] = useState(false);

  const loadDomains = async () => {
    if (!selectedId) return;
    setDomains(await api<Domain[]>(`/projects/${selectedId}/domains`));
  };

  useEffect(() => {
    void loadDomains();
  }, [selectedId]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedId) return;
    await api<Domain>(`/projects/${selectedId}/domains`, {
      method: "POST",
      body: JSON.stringify({ hostname, is_primary: primary })
    });
    setHostname("");
    setPrimary(false);
    await loadDomains();
  };

  const check = async (id: number) => {
    if (!selectedId) return;
    await api<Domain>(`/projects/${selectedId}/domains/${id}/check`, { method: "POST" });
    await loadDomains();
  };

  const makePrimary = async (id: number) => {
    if (!selectedId) return;
    await api<Domain>(`/projects/${selectedId}/domains/${id}`, { method: "PATCH", body: JSON.stringify({ is_primary: true }) });
    await loadDomains();
  };

  const remove = async (id: number) => {
    if (!selectedId) return;
    await api(`/projects/${selectedId}/domains/${id}`, { method: "DELETE" });
    await loadDomains();
  };

  if (error) return <div className="panel p-5 text-red-200">{error}</div>;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title">Dominios</h1>
        <p className="muted mt-1">Adicione dominios customizados, cheque DNS e defina o principal.</p>
      </div>
      {selectedProject ? <ProjectTabs projectId={selectedProject.id} /> : null}
      {loading ? <div className="panel p-5 text-apex-muted">Carregando projetos...</div> : null}
      <ProjectSelector projects={projects} selectedId={selectedId} onChange={setSelectedId} />
      {selectedId ? (
        <>
          <form className="panel flex flex-col gap-4 p-4 md:flex-row md:items-end" onSubmit={submit}>
            <label className="block flex-1">
              <span className="label">Dominio</span>
              <input className="field" value={hostname} onChange={(event) => setHostname(event.target.value)} placeholder="app.apextechnologies.com.br" />
            </label>
            <label className="flex items-center gap-2 pb-2 text-sm text-apex-muted">
              <input type="checkbox" checked={primary} onChange={(event) => setPrimary(event.target.checked)} />
              Principal
            </label>
            <button className="btn-primary">
              <Plus className="h-4 w-4" />
              Adicionar
            </button>
          </form>
          <div className="grid gap-3">
            {domains.map((domain) => (
              <div key={domain.id} className="panel flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="font-medium text-white">{domain.hostname}</div>
                  <div className="mt-1 text-xs text-apex-muted">
                    DNS: {domain.dns_status} - SSL: {domain.ssl_enabled ? "ativo" : "pendente"} {domain.is_primary ? "- principal" : ""}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button className="btn-secondary" onClick={() => void check(domain.id)}>
                    <RefreshCcw className="h-4 w-4" />
                    DNS
                  </button>
                  <button className="btn-secondary" onClick={() => void makePrimary(domain.id)}>
                    <CheckCircle2 className="h-4 w-4" />
                    Principal
                  </button>
                  <button className="btn-danger" onClick={() => void remove(domain.id)}>
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
            {domains.length === 0 ? <div className="panel p-5 text-apex-muted">Nenhum dominio customizado.</div> : null}
          </div>
        </>
      ) : null}
    </div>
  );
}
