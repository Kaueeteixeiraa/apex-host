import { useEffect, useState } from "react";
import { CheckCircle2, CreditCard, ShieldCheck, Zap } from "lucide-react";

import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
import { api, Plan } from "../lib/api";

export function Plans() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void api<Plan[]>("/plans").then(setPlans).catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar planos"));
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Billing-ready"
        title="Planos internos"
        description="Estrutura comercial preparada para limites, suporte, alta disponibilidade e backups mesmo antes de pagamentos."
        icon={CreditCard}
      />
      {error ? <FeedbackBanner type="error" message={error} /> : null}

      <div className="grid gap-4 lg:grid-cols-4">
        {plans.map((plan) => (
          <div key={plan.id} className={`panel relative overflow-hidden p-5 ${plan.highlighted ? "border-apex-cyan shadow-glow" : ""}`}>
            {plan.highlighted ? <div className="absolute right-3 top-3 rounded-full bg-apex-cyan/15 px-2 py-1 text-xs text-apex-cyan">Recomendado</div> : null}
            <div className="mb-4 grid h-11 w-11 place-items-center rounded-lg border border-apex-cyan/30 bg-apex-cyan/10 text-apex-cyan">
              {plan.id === "free" ? <Zap className="h-5 w-5" /> : <ShieldCheck className="h-5 w-5" />}
            </div>
            <h2 className="text-xl font-semibold text-white">{plan.name}</h2>
            <p className="muted mt-2 min-h-[44px]">{plan.description}</p>
            <div className="mt-4 text-sm text-apex-muted">{plan.audience}</div>
            <div className="mt-2 text-2xl font-semibold text-white">{plan.price_label}</div>

            <div className="mt-5 space-y-2 text-sm">
              {Object.entries(plan.limits).map(([key, value]) => (
                <div key={key} className="flex justify-between gap-3 rounded-md border border-apex-line bg-black/20 px-3 py-2">
                  <span className="text-apex-muted">{key}</span>
                  <span className="text-right text-white">{value === null ? "Ilimitado" : String(value)}</span>
                </div>
              ))}
            </div>

            <div className="mt-5 space-y-2">
              {plan.features.map((feature) => (
                <div key={feature} className="flex items-center gap-2 text-sm text-apex-text">
                  <CheckCircle2 className="h-4 w-4 text-apex-cyan" />
                  {feature}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
