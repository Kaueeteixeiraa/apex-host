import { useEffect, useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, Clock, RadioTower } from "lucide-react";

import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { api, formatDate, PublicStatus as PublicStatusData } from "../lib/api";

export function PublicStatus() {
  const [status, setStatus] = useState<PublicStatusData | null>(null);

  useEffect(() => {
    void api<PublicStatusData>("/public/status").then(setStatus);
  }, []);

  const overall = status?.overall_status || "loading";

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <PageHeader
        eyebrow="Apex Host Status"
        title="Status publico da plataforma"
        description="Visao operacional de API, worker, banco, nodes, projetos monitorados e incidentes recentes."
        icon={RadioTower}
      />

      <section className="panel p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              {overall === "operational" ? <CheckCircle2 className="h-6 w-6 text-emerald-300" /> : <AlertTriangle className="h-6 w-6 text-yellow-300" />}
              <h2 className="text-2xl font-semibold text-white">
                {overall === "operational" ? "Todos os sistemas operacionais" : "Operacao com atencao"}
              </h2>
            </div>
            <p className="muted mt-2">Atualizado automaticamente pelo health check do Apex Host.</p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-center">
            <div className="rounded-md border border-apex-line bg-black/20 p-3">
              <div className="text-2xl font-semibold text-white">{status?.uptime_24h ?? 0}%</div>
              <div className="text-xs text-apex-muted">24h</div>
            </div>
            <div className="rounded-md border border-apex-line bg-black/20 p-3">
              <div className="text-2xl font-semibold text-white">{status?.uptime_7d ?? 0}%</div>
              <div className="text-xs text-apex-muted">7d</div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <div className="panel p-4">
          <h2 className="mb-4 font-semibold text-white">Componentes</h2>
          <div className="space-y-2">
            {status?.components.map((component) => (
              <div key={`${component.name}-${component.detail}`} className="flex items-center justify-between gap-3 rounded-md border border-apex-line bg-black/20 p-3">
                <div>
                  <div className="font-medium text-white">{component.name}</div>
                  <div className="text-xs text-apex-muted">{component.detail}</div>
                </div>
                <StatusBadge status={component.status === "operational" ? "online" : component.status} />
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-4">
          <div className="panel p-4">
            <div className="mb-3 flex items-center gap-2 text-white">
              <AlertTriangle className="h-5 w-5 text-apex-cyan" />
              Incidentes recentes
            </div>
            <div className="space-y-2">
              {status?.incidents.map((incident) => (
                <div key={incident.id} className="rounded-md border border-apex-line bg-black/20 p-3">
                  <div className="text-sm font-medium text-white">{incident.message}</div>
                  <div className="mt-1 text-xs text-apex-muted">{formatDate(incident.created_at)}</div>
                </div>
              ))}
              {status && status.incidents.length === 0 ? <p className="muted">Nenhum incidente recente.</p> : null}
            </div>
          </div>
          <div className="panel p-4">
            <div className="mb-3 flex items-center gap-2 text-white">
              <Clock className="h-5 w-5 text-apex-cyan" />
              Historico
            </div>
            <div className="grid grid-cols-10 gap-1">
              {(status?.recent_checks || []).slice(0, 40).map((check) => (
                <div
                  key={check.id}
                  title={formatDate(check.checked_at)}
                  className={`h-7 rounded-sm ${check.status === "online" ? "bg-emerald-400/80" : "bg-red-400/80"}`}
                />
              ))}
            </div>
            {!status ? <div className="muted flex items-center gap-2"><Activity className="h-4 w-4" /> Carregando status...</div> : null}
          </div>
        </div>
      </section>
    </div>
  );
}
