import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Eye, EyeOff, KeyRound, Plus, Trash2 } from "lucide-react";

import { api, EnvVar, EnvVarReveal } from "../lib/api";
import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
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
  const [revealed, setRevealed] = useState<Record<number, string>>({});
  const [message, setMessage] = useState<string | null>(null);

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
    setMessage(`Variavel ${key} salva com seguranca.`);
    await load();
  };

  const remove = async (id: number) => {
    if (!selectedId) return;
    if (!confirm("Remover esta variavel de ambiente?")) return;
    await api(`/projects/${selectedId}/env/${id}`, { method: "DELETE" });
    await load();
  };

  const reveal = async (id: number) => {
    if (!selectedId) return;
    const data = await api<EnvVarReveal>(`/projects/${selectedId}/env/${id}/reveal`);
    setRevealed((current) => ({ ...current, [id]: data.value }));
    window.setTimeout(() => {
      setRevealed((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
    }, data.expires_in_seconds * 1000);
  };

  if (error) return <div className="panel p-5 text-red-200">{error}</div>;

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Secrets"
        title="Variaveis de ambiente"
        description="Valores sensiveis sao criptografados, mascarados por padrao e revelados apenas temporariamente com auditoria."
        icon={KeyRound}
      />
      {selectedProject ? <ProjectTabs projectId={selectedProject.id} /> : null}
      {message ? <FeedbackBanner type="success" message={message} /> : null}
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
                  <div className="mt-1 font-mono text-xs text-apex-muted">{revealed[item.id] || item.masked_value}</div>
                </div>
                <div className="flex gap-2">
                  {item.is_secret ? (
                    <button className="btn-secondary" onClick={() => (revealed[item.id] ? setRevealed(({ [item.id]: _, ...rest }) => rest) : void reveal(item.id))}>
                      {revealed[item.id] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      {revealed[item.id] ? "Ocultar" : "Revelar"}
                    </button>
                  ) : null}
                  <button className="btn-danger" onClick={() => void remove(item.id)}>
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
            {items.length === 0 ? <div className="p-5 text-apex-muted">Nenhuma variavel cadastrada.</div> : null}
          </div>
        </>
      ) : null}
    </div>
  );
}
