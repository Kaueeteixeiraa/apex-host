import { Github, ShieldCheck, Users } from "lucide-react";
import { useEffect, useState } from "react";

import { useAuth } from "../context/AuthContext";
import { api, AuditLog, formatDate, GitHubConnection } from "../lib/api";
import { PageHeader } from "../components/PageHeader";

export function Settings() {
  const { user } = useAuth();
  const [github, setGithub] = useState<GitHubConnection | null>(null);
  const [audit, setAudit] = useState<AuditLog[]>([]);

  useEffect(() => {
    void api<GitHubConnection>("/github/connection").then(setGithub).catch(() => setGithub({ connected: false, login: null, scope: null, connected_at: null }));
    void api<AuditLog[]>("/audit?limit=8").then(setAudit).catch(() => setAudit([]));
  }, []);

  const connectGithub = async () => {
    const data = await api<{ url: string }>("/github/oauth/start");
    window.location.href = data.url;
  };

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Control Room"
        title="Configuracoes"
        description="Conta, GitHub, flags de deploy, papeis de acesso e trilha de auditoria."
        icon={ShieldCheck}
      />

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="panel p-4">
          <div className="mb-4 flex items-center gap-2 text-white">
            <ShieldCheck className="h-5 w-5 text-apex-cyan" />
            Conta admin
          </div>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-apex-muted">Nome</dt>
              <dd className="text-white">{user?.full_name}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-apex-muted">Email</dt>
              <dd className="text-white">{user?.email}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-apex-muted">Plano</dt>
              <dd className="text-white">{user?.plan}</dd>
            </div>
          </dl>
        </div>
        <div className="panel p-4">
          <div className="mb-4 flex items-center gap-2 text-white">
            <Github className="h-5 w-5 text-apex-cyan" />
            GitHub
          </div>
          <p className="muted mb-4">
            {github?.connected ? `Conectado como ${github.login}` : "Conecte uma conta para listar repositorios e preparar webhooks."}
          </p>
          <button className="btn-primary" onClick={() => void connectGithub()}>
            <Github className="h-4 w-4" />
            {github?.connected ? "Reconectar GitHub" : "Conectar GitHub"}
          </button>
        </div>
        <div className="panel p-4">
          <h2 className="mb-3 font-semibold text-white">Flags de deploy</h2>
          <div className="space-y-2 text-sm text-apex-muted">
            <p>
              <code>ENABLE_DOCKER_DEPLOYS=true</code> ativa build/run real com Docker.
            </p>
            <p>
              <code>ENABLE_BUILD_COMMANDS=true</code> permite executar install/build do projeto.
            </p>
            <p>
              <code>NGINX_SITES_DIR</code> faz o backend escrever arquivos de proxy por projeto.
            </p>
            <p>
              <code>GITHUB_WEBHOOK_SECRET</code> valida webhooks com assinatura HMAC.
            </p>
          </div>
        </div>
      </section>

      <section className="panel p-4">
        <h2 className="mb-3 font-semibold text-white">Limites futuros</h2>
        <div className="grid gap-3 md:grid-cols-5">
          {["Projetos", "Deploys", "RAM", "Storage", "Dominios"].map((item) => (
            <div key={item} className="rounded-md border border-apex-line p-3">
              <div className="text-xs uppercase tracking-[0.12em] text-apex-muted">{item}</div>
              <div className="mt-2 text-white">Livre para admin</div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="panel p-4">
          <div className="mb-4 flex items-center gap-2 text-white">
            <Users className="h-5 w-5 text-apex-cyan" />
            Perfis preparados
          </div>
          <div className="grid gap-3">
            {[
              ["Admin", "Controle total da plataforma."],
              ["Dev", "Cria projetos, deploya e consulta logs."],
              ["Viewer", "Visualiza projetos liberados sem alterar configuracoes."]
            ].map(([role, description]) => (
              <div key={role} className="rounded-md border border-apex-line bg-black/20 p-3">
                <div className="font-medium text-white">{role}</div>
                <p className="mt-1 text-sm text-apex-muted">{description}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="panel p-4">
          <h2 className="mb-4 font-semibold text-white">Auditoria recente</h2>
          <div className="space-y-3">
            {audit.map((entry) => (
              <div key={entry.id} className="rounded-md border border-apex-line bg-black/20 p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium text-white">{entry.action}</span>
                  <span className="text-xs text-apex-muted">{formatDate(entry.created_at)}</span>
                </div>
                <div className="mt-1 text-xs text-apex-muted">
                  {entry.target_type || "system"} {entry.target_id ? `#${entry.target_id}` : ""}
                </div>
              </div>
            ))}
            {audit.length === 0 ? <p className="muted">Nenhum evento de auditoria registrado ainda.</p> : null}
          </div>
        </div>
      </section>
    </div>
  );
}
