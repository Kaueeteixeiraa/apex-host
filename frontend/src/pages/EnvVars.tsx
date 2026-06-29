import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Plus, Trash2 } from "lucide-react";

import { api, EnvVar } from "../lib/api";
import { ProjectSelector } from "../components/ProjectSelector";
import { ProjectTabs } from "../components/ProjectTabs";
import { useProjectScope } from "../lib/useProjectScope";

export function EnvVars() {
  const { projectId } = useParams();
  const { projects, selectedId, selectedProject, setSelectedId, loading, error } = useProjectScope(projectId);
  const [items, setItems] = useState<EnvVar[]>([]);
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [secret, setSecret] = useState(true);

  const load = async () => {
    if (!selectedId) return;
    setItems(await api<EnvVar[]>(`/projects/${selectedId}/env`));
  };

  useEffect(() => {
    void load();
  }, [selectedId]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedId) return;
    await api<EnvVar>(`/projects/${selectedId}/env`, {
      method: "POST",
      body: JSON.stringify({ key, value, is_secret: secret })
    });
    setKey("");
    setValue("");
    setSecret(true);
    await load();
  };

  const remove = async (id: number) => {
    if (!selectedId) return;
    await api(`/projects/${selectedId}/env/${id}`, { method: "DELETE" });
    await load();
  };

  if (error) return <div className="panel p-5 text-red-200">{error}</div>;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title">Variaveis de ambiente</h1>
        <p className="muted mt-1">Valores sensiveis sao criptografados no backend e mascarados na UI.</p>
      </div>
      {selectedProject ? <ProjectTabs projectId={selectedProject.id} /> : null}
      {loading ? <div className="panel p-5 text-apex-muted">Carregando projetos...</div> : null}
      <ProjectSelector projects={projects} selectedId={selectedId} onChange={setSelectedId} />
      {selectedId ? (
        <>
          <form className="panel grid gap-4 p-4 md:grid-cols-[220px_1fr_auto_auto]" onSubmit={submit}>
            <label>
              <span className="label">Chave</span>
              <input className="field" value={key} onChange={(event) => setKey(event.target.value.toUpperCase())} placeholder="DATABASE_URL" />
            </label>
            <label>
              <span className="label">Valor</span>
              <input className="field" value={value} onChange={(event) => setValue(event.target.value)} />
            </label>
            <label className="flex items-center gap-2 pb-2 text-sm text-apex-muted md:self-end">
              <input type="checkbox" checked={secret} onChange={(event) => setSecret(event.target.checked)} />
              Segredo
            </label>
            <button className="btn-primary md:self-end">
              <Plus className="h-4 w-4" />
              Adicionar
            </button>
          </form>
          <div className="panel overflow-hidden">
            {items.map((item) => (
              <div key={item.id} className="flex flex-col gap-3 border-b border-apex-line p-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="font-medium text-white">{item.key}</div>
                  <div className="mt-1 font-mono text-xs text-apex-muted">{item.masked_value}</div>
                </div>
                <button className="btn-danger" onClick={() => void remove(item.id)}>
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
            {items.length === 0 ? <div className="p-5 text-apex-muted">Nenhuma variavel cadastrada.</div> : null}
          </div>
        </>
      ) : null}
    </div>
  );
}
