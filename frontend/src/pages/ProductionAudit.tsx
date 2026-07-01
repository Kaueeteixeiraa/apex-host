import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";

import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
import { api, ProductionAudit as ProductionAuditType } from "../lib/api";

export function ProductionAudit() {
  const [audit, setAudit] = useState<ProductionAuditType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void api<ProductionAuditType>("/production-audit").then(setAudit).catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar auditoria"));
  }, []);

  if (error) return <FeedbackBanner type="error" message={error} />;
  if (!audit) return <div className="panel p-5 text-apex-muted">Carregando auditoria de producao...</div>;

  const tone = audit.status === "approved" ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-100" : audit.status === "critical" ? "border-red-400/30 bg-red-500/10 text-red-100" : "border-yellow-400/30 bg-yellow-400/10 text-yellow-100";

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Go Live"
        title="Auditoria de Producao"
        description="Checklist automatico para publicar o Apex Host em dominio real com Docker, Nginx, SSL, worker e backups."
        icon={ShieldAlert}
      />

      <section className={`panel border p-5 ${tone}`}>
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="section-title">Go Live - Producao Real</div>
            <h2 className="mt-2 text-3xl font-semibold text-white">{audit.summary}</h2>
            <p className="mt-2 text-sm opacity-85">{audit.critical_failures.length} falhas criticas encontradas.</p>
          </div>
          <div className="grid h-24 w-24 place-items-center rounded-full border border-current text-3xl font-semibold">
            {audit.score}%
          </div>
        </div>
      </section>

      {audit.critical_failures.length > 0 ? (
        <FeedbackBanner type="error" message={`Critico antes do Go Live: ${audit.critical_failures.slice(0, 4).join(", ")}${audit.critical_failures.length > 4 ? "..." : ""}`} />
      ) : null}

      <section className="grid gap-3 lg:grid-cols-2">
        {audit.items.map((item) => {
          const approved = item.status === "approved";
          const critical = item.status === "critical";
          const Icon = approved ? CheckCircle2 : AlertTriangle;
          return (
            <article key={item.id} className={`panel p-4 ${critical ? "border-red-400/30" : !approved ? "border-yellow-400/30" : ""}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Icon className={`h-5 w-5 ${approved ? "text-emerald-300" : critical ? "text-red-300" : "text-yellow-200"}`} />
                  <h2 className="font-semibold text-white">{item.label}</h2>
                </div>
                <span className={`rounded-full border px-2 py-0.5 text-xs ${approved ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-100" : critical ? "border-red-400/30 bg-red-400/10 text-red-100" : "border-yellow-400/30 bg-yellow-400/10 text-yellow-100"}`}>
                  {approved ? "Aprovado" : critical ? "Critico" : "Atencao"}
                </span>
              </div>
              {item.problem ? <p className="mt-3 text-sm text-red-100">{item.problem}</p> : null}
              <p className="mt-2 text-sm text-apex-muted">{item.why_it_matters}</p>
              {!approved ? <p className="mt-2 rounded-md border border-apex-line bg-black/20 p-3 text-sm text-apex-text">{item.fix}</p> : null}
            </article>
          );
        })}
      </section>
    </div>
  );
}
