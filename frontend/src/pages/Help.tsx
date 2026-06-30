import { BookOpen, ChevronRight } from "lucide-react";

import { PageHeader } from "../components/PageHeader";

const faqs = [
  ["Como criar projeto", "Abra Projetos, escolha GitHub ou template, valide build/start e inicie com dry run."],
  ["Como conectar GitHub", "Em Configuracoes, use Conectar GitHub para listar repositorios e preparar webhooks."],
  ["Como configurar dominio", "Cadastre o dominio no projeto, aponte DNS para a VPS e gere SSL quando Certbot estiver configurado."],
  ["Como ler logs", "Use Logs ou Deploys. Filtre por erro e acione Analisar erro para uma explicacao objetiva."],
  ["Como ativar fallback", "No projeto, abra Disponibilidade e habilite fallback estatico ou CDN/fallback externo."],
  ["Como funciona alta disponibilidade", "O Apex Host monitora health checks, pode reiniciar containers e prepara multi-node/CDN para reduzir queda."],
  ["Por que meu site caiu", "Normalmente por erro de build, env ausente, porta incorreta, VPS sem recurso ou dependencia quebrada."],
  ["Como fazer rollback", "Em Deploys, selecione um deploy bem-sucedido com commit e clique em Rollback."]
];

export function Help() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Knowledge Base"
        title="Ajuda Apex Host"
        description="Perguntas frequentes para operacao diaria, deploy, dominio, logs, fallback e alta disponibilidade."
        icon={BookOpen}
      />
      <div className="grid gap-4 lg:grid-cols-2">
        {faqs.map(([title, body]) => (
          <div key={title} className="panel p-4">
            <div className="mb-2 flex items-center gap-2 text-white">
              <ChevronRight className="h-4 w-4 text-apex-cyan" />
              <h2 className="font-semibold">{title}</h2>
            </div>
            <p className="muted">{body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
