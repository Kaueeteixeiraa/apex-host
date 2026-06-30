import { FormEvent, useEffect, useMemo, useState } from "react";
import { Boxes, Github, Globe2, KeyRound, LayoutTemplate, Plus, Rocket, SearchCheck, Settings2, Trash2 } from "lucide-react";

import { api, Deploy, Domain, EnvVar, FrameworkDetection, GitHubRepo, Project, ProjectTemplate } from "../lib/api";
import { EmptyState } from "../components/EmptyState";
import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
import { ProjectCard } from "../components/ProjectCard";

const emptyForm = {
  name: "",
  slug: "",
  github_url: "",
  branch: "main",
  project_type: "manual",
  install_command: "",
  build_command: "",
  start_command: "",
  output_directory: "",
  internal_port: 3000
};

const steps = [
  { id: 1, label: "Origem", icon: Github },
  { id: 2, label: "Build", icon: Settings2 },
  { id: 3, label: "Envs", icon: KeyRound },
  { id: 4, label: "Dominio", icon: Globe2 },
  { id: 5, label: "Deploy", icon: Rocket }
];

export function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [step, setStep] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [creationMode, setCreationMode] = useState<"github" | "template">("github");
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [detectionFiles, setDetectionFiles] = useState("package.json\nvite.config.ts\nsrc/App.tsx");
  const [detection, setDetection] = useState<FrameworkDetection | null>(null);
  const [loading, setLoading] = useState(false);
  const [envRows, setEnvRows] = useState([{ key: "", value: "", is_secret: true }]);
  const [customDomain, setCustomDomain] = useState("");
  const [triggerDeploy, setTriggerDeploy] = useState(true);

  const selectedRepo = useMemo(
    () => repos.find((repo) => repo.clone_url === form.github_url),
    [repos, form.github_url]
  );

  const load = async () => {
    setProjects(await api<Project[]>("/projects"));
  };

  useEffect(() => {
    void load().catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar projetos"));
    void api<GitHubRepo[]>("/github/repos").then(setRepos).catch(() => setRepos([]));
    void api<ProjectTemplate[]>("/templates").then(setTemplates).catch(() => setTemplates([]));
  }, []);

  const applyTemplate = (template: ProjectTemplate) => {
    setSelectedTemplateId(template.id);
    setForm({
      ...form,
      name: form.name || template.name,
      project_type: template.project_type,
      install_command: template.install_command || "",
      build_command: template.build_command || "",
      start_command: template.start_command || "",
      output_directory: template.output_directory || "",
      internal_port: template.internal_port
    });
    setMessage(`Template ${template.name} aplicado.`);
  };

  const detectFramework = async () => {
    const files = detectionFiles.split(/\r?\n|,/).map((item) => item.trim()).filter(Boolean);
    const result = await api<FrameworkDetection>("/templates/detect", {
      method: "POST",
      body: JSON.stringify({ files })
    });
    setDetection(result);
    setForm({
      ...form,
      project_type: result.project_type,
      install_command: result.install_command || "",
      build_command: result.build_command || "",
      start_command: result.start_command || "",
      output_directory: result.output_directory || "",
      internal_port: result.default_port
    });
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const project = await api<Project>("/projects", {
        method: "POST",
        body: JSON.stringify({
          name: form.name,
          slug: form.slug || null,
          github_url: form.github_url || null,
          branch: form.branch,
          project_type: form.project_type,
          install_command: form.install_command || null,
          build_command: form.build_command || null,
          start_command: form.start_command || null,
          github_repo_full_name: selectedRepo?.full_name || null,
          internal_port: form.internal_port
        })
      });

      for (const row of envRows.filter((item) => item.key.trim())) {
        await api<EnvVar>(`/projects/${project.id}/env`, {
          method: "POST",
          body: JSON.stringify({ key: row.key.trim().toUpperCase(), value: row.value, is_secret: row.is_secret })
        });
      }

      if (customDomain.trim()) {
        await api<Domain>(`/projects/${project.id}/domains`, {
          method: "POST",
          body: JSON.stringify({ hostname: customDomain.trim(), is_primary: true })
        });
      }

      if (triggerDeploy) {
        await api<Deploy>(`/projects/${project.id}/deploys`, {
          method: "POST",
          body: JSON.stringify({ dry_run: true })
        });
      }

      setForm(emptyForm);
      setEnvRows([{ key: "", value: "", is_secret: true }]);
      setCustomDomain("");
      setStep(1);
      setMessage(`Projeto ${project.name} criado com sucesso.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar projeto");
    } finally {
      setLoading(false);
    }
  };

  const remove = async (id: number) => {
    if (!confirm("Excluir este projeto? Esta acao remove historico, envs e dominios.")) return;
    await api(`/projects/${id}`, { method: "DELETE" });
    await load();
  };

  const quickDeploy = async (project: Project) => {
    const deploy = await api<Deploy>(`/projects/${project.id}/deploys`, {
      method: "POST",
      body: JSON.stringify({ dry_run: true })
    });
    setMessage(`Deploy dry run #${deploy.id} enfileirado para ${project.name}.`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Projects"
        title="Projetos"
        description="Crie projetos em um fluxo guiado, conecte GitHub, configure build, envs, dominios e deploy inicial."
        icon={Boxes}
      />

      {message ? <FeedbackBanner type="success" message={message} /> : null}
      {error ? <FeedbackBanner type="error" message={error} /> : null}

      <form className="panel overflow-hidden" onSubmit={submit}>
        <div className="border-b border-apex-line p-4">
          <div className="flex gap-2 overflow-x-auto">
            {steps.map((item) => {
              const Icon = item.icon;
              const active = step === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  className={`flex shrink-0 items-center gap-2 rounded-md border px-3 py-2 text-sm transition ${
                    active ? "border-apex-cyan bg-apex-cyan/10 text-white shadow-glow" : "border-apex-line text-apex-muted hover:text-white"
                  }`}
                  onClick={() => setStep(item.id)}
                >
                  <Icon className="h-4 w-4" />
                  {item.id}. {item.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="p-4">
          {step === 1 ? (
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <button
                  type="button"
                  className={`rounded-lg border p-4 text-left transition ${creationMode === "github" ? "border-apex-cyan bg-apex-cyan/10 shadow-glow" : "border-apex-line bg-black/20"}`}
                  onClick={() => setCreationMode("github")}
                >
                  <Github className="mb-2 h-5 w-5 text-apex-cyan" />
                  <div className="font-medium text-white">Importar do GitHub</div>
                  <p className="mt-1 text-sm text-apex-muted">Use repositorio conectado, URL manual e webhooks.</p>
                </button>
                <button
                  type="button"
                  className={`rounded-lg border p-4 text-left transition ${creationMode === "template" ? "border-apex-cyan bg-apex-cyan/10 shadow-glow" : "border-apex-line bg-black/20"}`}
                  onClick={() => setCreationMode("template")}
                >
                  <LayoutTemplate className="mb-2 h-5 w-5 text-apex-cyan" />
                  <div className="font-medium text-white">Criar usando template</div>
                  <p className="mt-1 text-sm text-apex-muted">Comece com stack, comandos e porta sugeridos.</p>
                </button>
              </div>

              {creationMode === "github" ? (
                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="rounded-lg border border-apex-cyan/30 bg-apex-cyan/10 p-4">
                <div className="mb-2 flex items-center gap-2 text-white">
                  <Github className="h-5 w-5 text-apex-cyan" />
                  GitHub
                </div>
                <p className="muted mb-4">Use um repositorio conectado ou informe a URL manualmente.</p>
                {repos.length > 0 ? (
                  <select
                    className="field"
                    onChange={(event) => {
                      const repo = repos.find((item) => item.full_name === event.target.value);
                      if (repo) setForm({ ...form, github_url: repo.clone_url, branch: repo.default_branch, name: form.name || repo.full_name.split("/")[1] });
                    }}
                    defaultValue=""
                  >
                    <option value="">Selecionar repositorio</option>
                    {repos.map((repo) => (
                      <option key={repo.full_name} value={repo.full_name}>
                        {repo.full_name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="rounded-md border border-apex-line bg-black/20 p-3 text-sm text-apex-muted">
                    GitHub OAuth nao conectado. A URL manual continua disponivel.
                  </div>
                )}
                  </div>
                  <div className="space-y-4">
                    <label>
                      <span className="label">URL do repositorio</span>
                      <input className="field" value={form.github_url} onChange={(event) => setForm({ ...form, github_url: event.target.value })} />
                    </label>
                    <label>
                      <span className="label">Branch</span>
                      <input className="field" value={form.branch} onChange={(event) => setForm({ ...form, branch: event.target.value })} />
                    </label>
                  </div>
                </div>
              ) : (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  {templates.map((template) => (
                    <button
                      key={template.id}
                      type="button"
                      className={`rounded-lg border p-4 text-left transition hover:-translate-y-0.5 hover:border-apex-cyan/60 ${
                        selectedTemplateId === template.id ? "border-apex-cyan bg-apex-cyan/10 shadow-glow" : "border-apex-line bg-black/20"
                      }`}
                      onClick={() => applyTemplate(template)}
                    >
                      <div className="mb-2 text-2xl">{template.icon}</div>
                      <div className="font-medium text-white">{template.name}</div>
                      <p className="mt-1 line-clamp-2 text-sm text-apex-muted">{template.description}</p>
                      <div className="mt-3 flex flex-wrap gap-1">
                        {template.tags.slice(0, 3).map((tag) => (
                          <span key={tag} className="rounded-full border border-apex-cyan/30 bg-apex-cyan/10 px-2 py-0.5 text-xs text-apex-cyan">{tag}</span>
                        ))}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : null}

          {step === 2 ? (
            <div className="grid gap-4 lg:grid-cols-4">
              <label className="lg:col-span-2">
                <span className="label">Nome</span>
                <input className="field" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
              </label>
              <label>
                <span className="label">Slug</span>
                <input className="field" value={form.slug} onChange={(event) => setForm({ ...form, slug: event.target.value })} placeholder="auto" />
              </label>
              <label>
                <span className="label">Framework</span>
                <select className="field" value={form.project_type} onChange={(event) => setForm({ ...form, project_type: event.target.value })}>
                  <option value="manual">manual</option>
                  <option value="react-vite">react-vite</option>
                  <option value="nextjs">nextjs</option>
                  <option value="node">node</option>
                  <option value="fastapi">fastapi</option>
                  <option value="flask">flask</option>
                  <option value="static">static</option>
                </select>
              </label>
              <label>
                <span className="label">Install</span>
                <input className="field" value={form.install_command} onChange={(event) => setForm({ ...form, install_command: event.target.value })} />
              </label>
              <label>
                <span className="label">Build</span>
                <input className="field" value={form.build_command} onChange={(event) => setForm({ ...form, build_command: event.target.value })} />
              </label>
              <label>
                <span className="label">Start</span>
                <input className="field" value={form.start_command} onChange={(event) => setForm({ ...form, start_command: event.target.value })} />
              </label>
              <label>
                <span className="label">Porta interna</span>
                <input className="field" type="number" value={form.internal_port} onChange={(event) => setForm({ ...form, internal_port: Number(event.target.value) })} />
              </label>
              <label className="lg:col-span-2">
                <span className="label">Output directory</span>
                <input
                  className="field"
                  value={form.output_directory}
                  onChange={(event) => setForm({ ...form, output_directory: event.target.value })}
                  placeholder="dist, build, .next - preparado para automacao futura"
                />
              </label>
              <div className="lg:col-span-4 rounded-lg border border-apex-line bg-black/20 p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <div className="font-medium text-white">Deteccao automatica de framework</div>
                    <p className="muted">Cole nomes de arquivos encontrados no repo para sugerir stack, comandos, output e porta.</p>
                  </div>
                  <button className="btn-secondary" type="button" onClick={() => void detectFramework()}>
                    <SearchCheck className="h-4 w-4" />
                    Detectar
                  </button>
                </div>
                <textarea className="field min-h-24" value={detectionFiles} onChange={(event) => setDetectionFiles(event.target.value)} />
                {detection ? (
                  <div className="mt-3 rounded-md border border-apex-cyan/30 bg-apex-cyan/10 p-3 text-sm text-apex-text">
                    <strong>{detection.framework}</strong> com {Math.round(detection.confidence * 100)}% de confianca. {detection.reasons.join(" ")}
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}

          {step === 3 ? (
            <div className="space-y-3">
              <FeedbackBanner type="info" message="Segredos sao criptografados no backend e nunca aparecem completos em listagens padrao." />
              {envRows.map((row, index) => (
                <div key={index} className="grid gap-3 md:grid-cols-[220px_1fr_auto_auto]">
                  <input
                    className="field"
                    value={row.key}
                    onChange={(event) => setEnvRows(envRows.map((item, itemIndex) => (itemIndex === index ? { ...item, key: event.target.value.toUpperCase() } : item)))}
                    placeholder="DATABASE_URL"
                  />
                  <input
                    className="field"
                    value={row.value}
                    onChange={(event) => setEnvRows(envRows.map((item, itemIndex) => (itemIndex === index ? { ...item, value: event.target.value } : item)))}
                    placeholder="valor"
                  />
                  <label className="flex items-center gap-2 text-sm text-apex-muted">
                    <input
                      type="checkbox"
                      checked={row.is_secret}
                      onChange={(event) => setEnvRows(envRows.map((item, itemIndex) => (itemIndex === index ? { ...item, is_secret: event.target.checked } : item)))}
                    />
                    Segredo
                  </label>
                  <button className="btn-danger" type="button" onClick={() => setEnvRows(envRows.filter((_, itemIndex) => itemIndex !== index))}>
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
              <button className="btn-secondary" type="button" onClick={() => setEnvRows([...envRows, { key: "", value: "", is_secret: true }])}>
                <Plus className="h-4 w-4" />
                Adicionar variavel
              </button>
            </div>
          ) : null}

          {step === 4 ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <label>
                <span className="label">Dominio customizado opcional</span>
                <input className="field" value={customDomain} onChange={(event) => setCustomDomain(event.target.value)} placeholder="app.apextechnologies.com.br" />
              </label>
              <div className="rounded-lg border border-apex-line bg-black/20 p-4">
                <div className="section-title mb-2">DNS</div>
                <p className="muted">Apex Host gera um subdominio interno automatico. Para dominio customizado, aponte CNAME para o host da plataforma ou A record para o IP da VPS.</p>
              </div>
            </div>
          ) : null}

          {step === 5 ? (
            <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
              <div className="terminal p-4">
                <div className="text-apex-cyan">$ apex deploy --project {form.slug || form.name || "novo-projeto"}</div>
                <div className="mt-2 text-apex-muted">1. Clonar repositorio</div>
                <div className="text-apex-muted">2. Validar comandos permitidos</div>
                <div className="text-apex-muted">3. Aplicar variaveis criptografadas</div>
                <div className="text-apex-muted">4. Executar dry run seguro por padrao</div>
              </div>
              <div className="rounded-lg border border-apex-line bg-black/20 p-4">
                <label className="flex items-center gap-2 text-sm text-apex-muted">
                  <input type="checkbox" checked={triggerDeploy} onChange={(event) => setTriggerDeploy(event.target.checked)} />
                  Iniciar deploy dry run apos criar
                </label>
                <button className="btn-primary mt-4 w-full" disabled={loading}>
                  <Rocket className="h-4 w-4" />
                  {loading ? "Criando..." : "Criar projeto"}
                </button>
              </div>
            </div>
          ) : null}
        </div>

        <div className="flex justify-between border-t border-apex-line p-4">
          <button className="btn-secondary" type="button" disabled={step === 1} onClick={() => setStep(Math.max(1, step - 1))}>
            Voltar
          </button>
          {step < 5 ? (
            <button className="btn-primary" type="button" onClick={() => setStep(Math.min(5, step + 1))}>
              Continuar
            </button>
          ) : null}
        </div>
      </form>

      {projects.length > 0 ? (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-white">Projetos cadastrados</h2>
            <span className="text-sm text-apex-muted">{projects.length} projetos</span>
          </div>
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {projects.map((project) => (
              <div key={project.id} className="relative">
                <ProjectCard project={project} onDeploy={(item) => void quickDeploy(item)} />
                <button className="absolute right-3 top-14 rounded-md border border-red-500/30 bg-red-500/10 p-2 text-red-200 hover:bg-red-500/20" onClick={() => void remove(project.id)}>
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <EmptyState icon={Boxes} title="Nenhum projeto cadastrado" description="Use o wizard acima para criar seu primeiro deploy controlado." />
      )}
    </div>
  );
}
