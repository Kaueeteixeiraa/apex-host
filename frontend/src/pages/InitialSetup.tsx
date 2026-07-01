import { FormEvent, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { CheckCircle2, Rocket, ShieldCheck } from "lucide-react";

import { ApexLogo } from "../components/ApexLogo";
import { FeedbackBanner } from "../components/FeedbackBanner";
import { api, ProductionAuditItem, setToken, SetupStatus } from "../lib/api";
import { useAuth } from "../context/AuthContext";

export function InitialSetup() {
  const { refreshUser, user } = useAuth();
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [step, setStep] = useState(1);
  const [checks, setChecks] = useState<ProductionAuditItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [form, setForm] = useState({
    platform_name: "Apex Host",
    company_name: "Apex Technologies",
    base_domain: "",
    public_app_url: "",
    contact_email: "",
    full_name: "",
    email: "",
    password: "",
    confirm_password: ""
  });

  useEffect(() => {
    void api<SetupStatus>("/setup/status").then(setStatus).catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar setup"));
  }, []);

  useEffect(() => {
    if (step !== 3) return;
    void api<{ items: ProductionAuditItem[] }>("/setup/validate").then((data) => setChecks(data.items)).catch(() => setChecks([]));
  }, [step]);

  if (user || done) return <Navigate to="/" replace />;
  if (status && !status.needs_setup) return <Navigate to="/login" replace />;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (step < 4) {
      setStep(step + 1);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const token = await api<{ access_token: string }>("/setup/complete", {
        method: "POST",
        body: JSON.stringify({
          platform: {
            platform_name: form.platform_name,
            company_name: form.company_name,
            base_domain: form.base_domain,
            public_app_url: form.public_app_url,
            contact_email: form.contact_email
          },
          admin: {
            full_name: form.full_name,
            email: form.email,
            password: form.password,
            confirm_password: form.confirm_password
          }
        })
      });
      setToken(token.access_token);
      await refreshUser();
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao concluir instalacao");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="apex-grid grid min-h-screen place-items-center px-4 py-8">
      <form className="panel w-full max-w-4xl overflow-hidden" onSubmit={submit}>
        <div className="border-b border-apex-line p-5">
          <div className="flex items-center gap-4">
            <ApexLogo className="h-14 w-14" animated />
            <div>
              <div className="section-title">Go Live - Producao Real</div>
              <h1 className="text-2xl font-semibold text-white">Bem-vindo ao Apex Host</h1>
              <p className="muted mt-1">Configure a plataforma e crie o primeiro Admin seguro.</p>
            </div>
          </div>
          <div className="mt-5 grid gap-2 sm:grid-cols-4">
            {["Plataforma", "Primeiro Admin", "Validar ambiente", "Finalizar"].map((label, index) => (
              <div key={label} className={`rounded-md border px-3 py-2 text-sm ${step === index + 1 ? "border-apex-cyan bg-apex-cyan/10 text-white shadow-glow" : "border-apex-line text-apex-muted"}`}>
                {index + 1}. {label}
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4 p-5">
          {error ? <FeedbackBanner type="error" message={error} /> : null}

          {step === 1 ? (
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Nome da plataforma" value={form.platform_name} onChange={(value) => setForm({ ...form, platform_name: value })} />
              <Field label="Nome da empresa" value={form.company_name} onChange={(value) => setForm({ ...form, company_name: value })} />
              <Field label="Dominio base" value={form.base_domain} placeholder="apextechnologies.com.br" onChange={(value) => setForm({ ...form, base_domain: value })} />
              <Field label="URL publica do painel" value={form.public_app_url} placeholder="https://host.apextechnologies.com.br" onChange={(value) => setForm({ ...form, public_app_url: value })} />
              <Field label="E-mail de contato/admin" value={form.contact_email} onChange={(value) => setForm({ ...form, contact_email: value })} />
            </div>
          ) : null}

          {step === 2 ? (
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Nome" value={form.full_name} onChange={(value) => setForm({ ...form, full_name: value })} />
              <Field label="E-mail" value={form.email} onChange={(value) => setForm({ ...form, email: value })} />
              <Field label="Senha" type="password" value={form.password} onChange={(value) => setForm({ ...form, password: value })} />
              <Field label="Confirmar senha" type="password" value={form.confirm_password} onChange={(value) => setForm({ ...form, confirm_password: value })} />
              <div className="md:col-span-2 rounded-md border border-apex-cyan/30 bg-apex-cyan/10 p-3 text-sm text-apex-text">
                O primeiro Admin so pode ser criado aqui enquanto nao existir Admin no banco. Cadastro publico nao ganha Admin livremente.
              </div>
            </div>
          ) : null}

          {step === 3 ? (
            <div className="grid gap-3 md:grid-cols-2">
              {checks.length === 0 ? <p className="muted md:col-span-2">Carregando validacoes...</p> : null}
              {checks.map((item) => (
                <div key={item.id} className="rounded-md border border-apex-line bg-black/20 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-white">{item.label}</span>
                    <Status status={item.status} />
                  </div>
                  {item.problem ? <p className="mt-2 text-sm text-apex-muted">{item.fix}</p> : null}
                </div>
              ))}
            </div>
          ) : null}

          {step === 4 ? (
            <div className="rounded-lg border border-apex-cyan/30 bg-apex-cyan/10 p-5">
              <div className="flex items-center gap-3 text-white">
                <ShieldCheck className="h-6 w-6 text-apex-cyan" />
                Instalar Apex Host
              </div>
              <p className="muted mt-2">Ao finalizar, o Admin sera criado, a instalacao sera marcada como concluida e voce entrara no Dashboard.</p>
            </div>
          ) : null}
        </div>

        <div className="flex justify-between border-t border-apex-line p-5">
          <button className="btn-secondary" type="button" disabled={step === 1 || loading} onClick={() => setStep(Math.max(1, step - 1))}>
            Voltar
          </button>
          <button className="btn-primary" disabled={loading}>
            {step === 4 ? <CheckCircle2 className="h-4 w-4" /> : <Rocket className="h-4 w-4" />}
            {loading ? "Finalizando..." : step === 4 ? "Finalizar instalacao" : "Continuar"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, value, onChange, placeholder, type = "text" }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; type?: string }) {
  return (
    <label>
      <span className="label">{label}</span>
      <input className="field" type={type} value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} required />
    </label>
  );
}

function Status({ status }: { status: string }) {
  const tone = status === "approved" ? "text-emerald-200 border-emerald-400/30 bg-emerald-400/10" : status === "critical" ? "text-red-100 border-red-400/30 bg-red-400/10" : "text-yellow-100 border-yellow-400/30 bg-yellow-400/10";
  const label = status === "approved" ? "Aprovado" : status === "critical" ? "Critico" : "Atencao";
  return <span className={`rounded-full border px-2 py-0.5 text-xs ${tone}`}>{label}</span>;
}
