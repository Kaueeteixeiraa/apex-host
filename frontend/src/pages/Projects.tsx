import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Atom,
  Boxes,
  Dices,
  FileCode2,
  FlaskConical,
  Gauge,
  Gem,
  Github,
  Globe2,
  KeyRound,
  LayoutTemplate,
  Plus,
  Rocket,
  Search,
  SearchCheck,
  Server,
  Settings2,
  Sparkles,
  Trash2,
  Triangle
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { api, Deploy, Domain, EnvVar, FrameworkDetection, GitHubRepo, Project, ProjectTemplate, PublicPlatform } from "../lib/api";
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
  internal_port: 3000,
  cpu_limit: "",
  memory_limit: ""
};

const templateIcons: Record<string, LucideIcon> = {
  Atom,
  Dices,
  FileCode2,
  FlaskConical,
  Gauge,
  Gem,
  Server,
  Sparkles,
  Triangle
};

const parseGitHubFullName = (url: string) => {
  const normalized = url.trim().replace(/\.git$/i, "").replace(/^git@github\.com:/i, "https://github.com/");
  const match = normalized.match(/github\.com\/([^/]+\/[^/]+)$/i);
  return match?.[1] || null;
};

const steps = [
  { id: 1, label: "Origem", icon: Github },
  { id: 2, label: "Configuracao", icon: Settings2 },
  { id: 3, label: "Variaveis", icon: KeyRound },
  { id: 4, label: "Dominio", icon: Globe2 },
  { id: 5, label: "Revisao/Deploy", icon: Rocket }
];

export function Projects() {
  const location = useLocation();
  const isNewRoute = location.pathname.endsWith("/new");
  const [projects, setProjects] = useState<Project[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [step, setStep] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [platform, setPlatform] = useState<PublicPlatform | null>(null);
  const [creationMode, setCreationMode] = useState<"github" | "template" | "internal">("github");
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [autoAppliedTemplate, setAutoAppliedTemplate] = useState("");
  const [detectionFiles, setDetectionFiles] = useState("package.json\nvite.config.ts\nsrc/App.tsx");
  const [detection, setDetection] = useState<FrameworkDetection | null>(null);
  const [loading, setLoading] = useState(false);
  const [envRows, setEnvRows] = useState([{ key: "", value: "", is_secret: true }]);
  const [customDomain, setCustomDomain] = useState("");
  const [triggerDeploy, setTriggerDeploy] = useState(true);
  const [projectSearch, setProjectSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const selectedRepo = useMemo(
    () => repos.find((repo) => repo.clone_url === form.github_url),
    [repos, form.github_url]
  );

  const filteredProjects = useMemo(() => {
    const search = projectSearch.toLowerCase().trim();
    return projects.filter((project) => {
      const matchesStatus = statusFilter === "all" || project.status === statusFilter;
      const matchesSearch = !search || `${project.name} ${project.slug} ${project.github_url || ""} ${project.auto_subdomain || ""}`.toLowerCase().includes(search);
      return matchesStatus && matchesSearch;
    });
  }, [projects, projectSearch, statusFilter]);

  const visibleTemplates = useMemo(
    () => templates.filter((template) => creationMode === "internal" ? template.is_internal : !template.is_internal),
    [templates, creationMode]
  );

  const load = async () => {
    setProjects(await api<Project[]>("/projects"));
  };

  useEffect(() => {
    void load().catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar projetos"));
    void api<GitHubRepo[]>("/github/repos").then(setRepos).catch(() => setRepos([]));
    void api<ProjectTemplate[]>("/templates").then(setTemplates).catch(() => setTemplates([]));
    void api<PublicPlatform>("/public/platform").then(setPlatform).catch(() => setPlatform(null));
  }, []);

  const hasUnsavedProjectForm = isNewRoute && (
    form.name.trim() ||
    form.slug.trim() ||
    form.github_url.trim() ||
    envRows.some((row) => row.key.trim() || row.value.trim()) ||
    customDomain.trim()
  );

  useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (!hasUnsavedProjectForm) return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", beforeUnload);
    return () => window.removeEventListener("beforeunload", beforeUnload);
  }, [hasUnsavedProjectForm]);

  const resolveSuggestedDomain = (template: ProjectTemplate) => {
    if (!template.suggested_domain) return "";
    return template.suggested_domain.replace("{BASE_DOMAIN}", platform?.base_domain || "apps.example.com");
  };

  const applyTemplate = (template: ProjectTemplate) => {
    setSelectedTemplateId(template.id);
    const suggestedDomain = resolveSuggestedDomain(template);
    setForm({
      ...form,
      name: form.name || template.name,
      slug: form.slug || (template.id === "apex-realms" ? "realms" : ""),
      github_url: template.github_url || form.github_url,
      branch: template.branch || form.branch || "main",
      project_type: template.project_type,
      install_command: template.install_command || "",
      build_command: template.build_command || "",
      start_command: template.start_command || "",
      output_directory: template.output_directory || "",
      internal_port: template.internal_port,
      cpu_limit: form.cpu_limit,
      memory_limit: form.memory_limit
    });
    if (suggestedDomain) setCustomDomain(suggestedDomain);
    if (template.id === "apex-realms") {
      setDetectionFiles("requirements.txt\napp.py\nProcfile\nwsgi.py\ntemplates/landing.html\nstatic/css");
    }
    setMessage(`Template ${template.name} aplicado.`);
  };

  useEffect(() => {
    if (!templates.length || autoAppliedTemplate) return;
    const requestedTemplate = new URLSearchParams(location.search).get("template");
    if (!requestedTemplate) return;
    const template = templates.find((item) => item.id === requestedTemplate);
    if (!template) return;
    setCreationMode(template.is_internal ? "internal" : "template");
    applyTemplate(template);
    setAutoAppliedTemplate(template.id);
  }, [templates, location.search, autoAppliedTemplate, platform]);

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
      internal_port: result.default_port,
      cpu_limit: form.cpu_limit,
      memory_limit: form.memory_limit
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
          output_directory: form.output_directory || null,
          github_repo_full_name: selectedRepo?.full_name || parseGitHubFullName(form.github_url),
          cpu_limit: form.cpu_limit || null,
          memory_limit: form.memory_limit || null,
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
          body: JSON.stringify({})
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
      body: JSON.stringify({})
    });
    setMessage(`Deploy #${deploy.id} enfileirado para ${project.name}.`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Projetos Apex"
        title={isNewRoute ? "Criar projeto" : "Projetos"}
        description={isNewRoute ? "Fluxo em etapas para origem, configuracao, variaveis, dominio e revisao de deploy." : "Lista de projetos internos hospedados na infraestrutura privada Apex."}
        icon={Boxes}
        actions={
          isNewRoute ? (
            <Link className="btn-secondary" to="/projects" onClick={(event) => {
              if (hasUnsavedProjectForm && !window.confirm("Descartar formulario de projeto nao salvo?")) event.preventDefault();
            }}>
              <ArrowLeft className="h-4 w-4" />
              Voltar para projetos
            </Link>
          ) : null
        }
      />

      {message ? <FeedbackBanner type="success" message={message} /> : null}
      {error ? <FeedbackBanner type="error" message={error} /> : null}

      {isNewRoute ? (
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
              <div className="grid gap-3 lg:grid-cols-3">
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
                <button
                  type="button"
                  className={`rounded-lg border p-4 text-left transition ${creationMode === "internal" ? "border-apex-cyan bg-apex-cyan/10 shadow-glow" : "border-apex-line bg-black/20"}`}
                  onClick={() => setCreationMode("internal")}
                >
                  <Dices className="mb-2 h-5 w-5 text-apex-cyan" />
                  <div className="font-medium text-white">Projeto interno Apex</div>
                  <p className="mt-1 text-sm text-apex-muted">Publique projetos oficiais da Apex, comecando pelo Apex Realms.</p>
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
                  {visibleTemplates.map((template) => {
                    const Icon = templateIcons[template.icon] || LayoutTemplate;
                    const isApexRealms = template.id === "apex-realms";
                    return (
                    <button
                      key={template.id}
                      type="button"
                      className={`rounded-lg border p-4 text-left transition hover:-translate-y-0.5 hover:border-apex-cyan/60 ${
                        selectedTemplateId === template.id ? "border-apex-cyan bg-apex-cyan/10 shadow-glow" : "border-apex-line bg-black/20"
                      }`}
                      onClick={() => applyTemplate(template)}
                    >
                      <div className="mb-3 flex items-start justify-between gap-2">
                        <div className="grid h-10 w-10 place-items-center rounded-lg border border-apex-cyan/30 bg-apex-cyan/10 text-apex-cyan">
                          <Icon className="h-5 w-5" />
                        </div>
                        {template.is_internal ? (
                          <span className="rounded-full border border-apex-cyan/30 bg-apex-cyan/10 px-2 py-0.5 text-[11px] uppercase tracking-[0.12em] text-apex-cyan">
                            Projeto interno
                          </span>
                        ) : null}
                      </div>
                      <div className="font-medium text-white">{template.name}</div>
                      {template.category ? <div className="mt-1 text-xs text-apex-cyan">{template.category}</div> : null}
                      <p className="mt-1 line-clamp-2 text-sm text-apex-muted">{template.description}</p>
                      {template.github_url ? <p className="mt-2 truncate text-xs text-apex-muted">{template.github_url}</p> : null}
                      <div className="mt-3 flex flex-wrap gap-1">
                        {template.tags.slice(0, 3).map((tag) => (
                          <span key={tag} className="rounded-full border border-apex-cyan/30 bg-apex-cyan/10 px-2 py-0.5 text-xs text-apex-cyan">{tag}</span>
                        ))}
                      </div>
                      {isApexRealms ? (
                        <div className="mt-4 rounded-md bg-apex-cyan px-3 py-2 text-center text-sm font-semibold text-black shadow-glow">
                          Deploy Apex Realms
                        </div>
                      ) : null}
                    </button>
                    );
                  })}
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
              <label>
                <span className="label">CPU max.</span>
                <input className="field" value={form.cpu_limit} onChange={(event) => setForm({ ...form, cpu_limit: event.target.value })} placeholder="0.50 ou vazio" />
              </label>
              <label>
                <span className="label">RAM max.</span>
                <input className="field" value={form.memory_limit} onChange={(event) => setForm({ ...form, memory_limit: event.target.value })} placeholder="512m ou 1g" />
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
                <input className="field" value={customDomain} onChange={(event) => setCustomDomain(event.target.value)} placeholder="realms.apps.seudominio.com" />
              </label>
              <div className="rounded-lg border border-apex-line bg-black/20 p-4">
                <div className="section-title mb-2">DNS</div>
                <p className="muted">Apex Host gera um subdominio interno automatico. Para dominio customizado, aponte CNAME para o host da plataforma ou A record para o IP da VPS.</p>
                {selectedTemplateId === "apex-realms" ? (
                  <div className="mt-3 rounded-md border border-apex-cyan/30 bg-apex-cyan/10 p-3 text-sm text-apex-text">
                    Dominio sugerido para Apex Realms: <strong>{customDomain || `realms.${platform?.base_domain || "apps.example.com"}`}</strong>
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}

          {step === 5 ? (
            <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
              <div className="terminal p-4">
                <div className="text-apex-cyan">$ apex deploy --project {form.slug || form.name || "novo-projeto"}</div>
                <div className="mt-2 text-apex-muted">1. Preparando ambiente</div>
                <div className="text-apex-muted">2. Clonando repositorio</div>
                <div className="text-apex-muted">3. Detectando stack</div>
                <div className="text-apex-muted">4. Instalando dependencias</div>
                <div className="text-apex-muted">5. Rodando build</div>
                <div className="text-apex-muted">6. Criando container</div>
                <div className="text-apex-muted">7. Configurando Nginx</div>
                <div className="text-apex-muted">8. Gerando SSL</div>
                <div className="text-apex-muted">9. Rodando health check</div>
                <div className="text-apex-muted">10. Publicando projeto</div>
              </div>
              <div className="rounded-lg border border-apex-line bg-black/20 p-4">
                <label className="flex items-center gap-2 text-sm text-apex-muted">
                  <input type="checkbox" checked={triggerDeploy} onChange={(event) => setTriggerDeploy(event.target.checked)} />
                  Iniciar deploy apos criar
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
      ) : null}

      {!isNewRoute && projects.length > 0 ? (
        <section>
          <div className="mb-3 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="font-semibold text-white">Projetos hospedados</h2>
              <p className="text-sm text-apex-muted">{filteredProjects.length} de {projects.length} projetos visiveis</p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <div className="relative min-w-64">
                <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-apex-muted" />
                <input className="field pl-9" value={projectSearch} onChange={(event) => setProjectSearch(event.target.value)} placeholder="Buscar projeto, dominio ou repo" />
              </div>
              <select className="field sm:w-44" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="all">Todos</option>
                <option value="online">Online</option>
                <option value="offline">Offline</option>
                <option value="building">Deployando</option>
                <option value="error">Com erro</option>
              </select>
            </div>
          </div>
          {filteredProjects.length > 0 ? (
            <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
              {filteredProjects.map((project) => (
              <div key={project.id} className="relative">
                <ProjectCard project={project} onDeploy={(item) => void quickDeploy(item)} />
                <button className="absolute right-3 top-14 rounded-md border border-red-500/30 bg-red-500/10 p-2 text-red-200 hover:bg-red-500/20" onClick={() => void remove(project.id)}>
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              ))}
            </div>
          ) : (
            <EmptyState icon={SearchCheck} title="Nenhum projeto encontrado" description="Ajuste a busca ou o filtro de status para ver outros projetos hospedados." />
          )}
        </section>
      ) : null}

      {!isNewRoute && projects.length === 0 ? (
        <EmptyState
          icon={Boxes}
          title="Nenhum projeto hospedado ainda"
          description="Comece validando o Apex Host com um projeto interno da Apex."
          action={
            <div className="flex flex-wrap justify-center gap-2">
              <Link className="btn-primary" to="/projects/new?template=apex-realms">
                <Dices className="h-4 w-4" />
                Hospedar Apex Realms
              </Link>
              <Link className="btn-secondary" to="/projects/new">
                <Plus className="h-4 w-4" />
                Criar projeto manualmente
              </Link>
            </div>
          }
        />
      ) : null}

      {isNewRoute && projects.length > 0 ? (
        <div className="panel p-4 text-sm text-apex-muted">
          Depois de criar, o projeto aparece automaticamente na lista principal.
        </div>
      ) : null}
    </div>
  );
}
