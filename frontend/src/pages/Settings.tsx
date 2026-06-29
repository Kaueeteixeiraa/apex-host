import { ShieldCheck } from "lucide-react";

import { useAuth } from "../context/AuthContext";

export function Settings() {
  const { user } = useAuth();

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title">Configuracoes</h1>
        <p className="muted mt-1">Base administrativa e parametros para crescer para planos e usuarios.</p>
      </div>

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
    </div>
  );
}
