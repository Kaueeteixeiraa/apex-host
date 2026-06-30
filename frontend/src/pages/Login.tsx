import { FormEvent, useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import { Github, LockKeyhole, Mail, Sparkles, UserPlus } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { ApexLogo } from "../components/ApexLogo";
import { FeedbackBanner } from "../components/FeedbackBanner";

type Mode = "login" | "register";

export function Login() {
  const { login, register, user } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("admin@apex.local");
  const [password, setPassword] = useState("apex-admin");
  const [fullName, setFullName] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [accountType, setAccountType] = useState<"admin" | "dev" | "client">("client");
  const [adminCode, setAdminCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [redirect, setRedirect] = useState(false);

  useEffect(() => {
    if (!loading) return;
    const interval = window.setInterval(() => {
      setProgress((current) => Math.min(current + Math.ceil(Math.random() * 12), 96));
    }, 130);
    return () => window.clearInterval(interval);
  }, [loading]);

  const passwordScore = useMemo(() => {
    let score = 0;
    if (password.length >= 8) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    return score;
  }, [password]);

  if (user && !loading) return <Navigate to="/" replace />;
  if (user && redirect) return <Navigate to="/" replace />;

  const switchMode = (next: Mode) => {
    setMode(next);
    setError(null);
    setSuccess(null);
    setProgress(0);
    if (next === "register") {
      setPassword("");
      setEmail("");
    } else {
      setEmail(email || "admin@apex.local");
      setPassword(password || "apex-admin");
    }
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setProgress(12);
    setError(null);
    setSuccess(null);
    try {
      if (mode === "login") {
        await login(email, password);
        setSuccess("Login aprovado. Abrindo painel...");
      } else {
        if (password !== confirmPassword) throw new Error("As senhas nao conferem.");
        await register({
          full_name: fullName,
          email,
          password,
          confirm_password: confirmPassword,
          account_type: accountType,
          admin_signup_code: adminCode || undefined
        });
        setSuccess(accountType === "admin" && !adminCode ? "Conta criada como Cliente e enviada para revisao de admin." : "Conta criada. Abrindo dashboard...");
      }
      setProgress(100);
      window.setTimeout(() => setRedirect(true), 520);
    } catch (err) {
      setError(err instanceof Error ? err.message : mode === "login" ? "Falha no login" : "Falha no cadastro");
      setProgress(0);
      setLoading(false);
    }
  };

  return (
    <div className="apex-grid relative grid min-h-screen place-items-center overflow-hidden px-4 py-8">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[8%] top-[12%] h-56 w-56 rounded-full bg-apex-blue/20 blur-3xl" />
        <div className="absolute bottom-[8%] right-[10%] h-64 w-64 rounded-full bg-apex-cyan/15 blur-3xl" />
        <div className="absolute inset-x-0 top-1/3 h-px bg-gradient-to-r from-transparent via-apex-cyan/50 to-transparent" />
      </div>

      <div className="relative z-10 grid w-full max-w-6xl gap-6 lg:grid-cols-[1fr_460px] lg:items-center">
        <section className="hidden lg:block">
          <div className="mb-6 flex items-center gap-4">
            <div className="relative grid h-28 w-28 place-items-center">
              {loading ? <div className="energy-ring absolute inset-0 rounded-full border border-apex-cyan/30 border-t-apex-cyan shadow-glow" /> : null}
              <ApexLogo className="h-24 w-24" animated={loading} />
            </div>
            <div>
              <div className="section-title">Apex Host</div>
              <h1 className="mt-2 text-5xl font-semibold tracking-[0.14em] text-white">CONTROL PLANE</h1>
            </div>
          </div>
          <p className="max-w-xl text-lg text-apex-muted">
            Uma entrada segura, elegante e preparada para times: login, cadastro, OAuth futuro e aprovacao de papeis sensiveis.
          </p>
          <div className="mt-8 grid max-w-2xl gap-3 sm:grid-cols-3">
            {["Deploys seguros", "Blue/green", "Auditoria"].map((item) => (
              <div key={item} className="rounded-lg border border-apex-line bg-white/5 p-4 text-sm text-apex-text backdrop-blur">
                <Sparkles className="mb-3 h-5 w-5 text-apex-cyan" />
                {item}
              </div>
            ))}
          </div>
        </section>

        <section className="w-full">
          <div className="mb-6 flex flex-col items-center text-center lg:hidden">
            <ApexLogo className="h-24 w-24" animated={loading} />
            <h1 className="mt-3 text-3xl font-semibold tracking-[0.16em] text-white">APEX HOST</h1>
            <p className="text-sm text-apex-muted">Painel privado de hospedagem Apex</p>
          </div>

          <form className="panel space-y-4 p-5 transition-all duration-500" onSubmit={onSubmit}>
            <div className="grid grid-cols-2 gap-2 rounded-lg border border-apex-line bg-black/20 p-1">
              <button type="button" className={mode === "login" ? "btn-primary" : "btn-secondary"} onClick={() => switchMode("login")}>
                <LockKeyhole className="h-4 w-4" />
                Login
              </button>
              <button type="button" className={mode === "register" ? "btn-primary" : "btn-secondary"} onClick={() => switchMode("register")}>
                <UserPlus className="h-4 w-4" />
                Cadastro
              </button>
            </div>

            {mode === "register" ? (
              <label className="stagger-in block">
                <span className="label">Nome</span>
                <input className={`field ${fullName && fullName.length < 2 ? "border-red-400" : ""}`} value={fullName} onChange={(event) => setFullName(event.target.value)} required />
              </label>
            ) : null}

            <label className="block">
              <span className="label">E-mail</span>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-apex-muted" />
                <input className={`field pl-9 ${email && !email.includes("@") ? "border-red-400" : ""}`} value={email} onChange={(event) => setEmail(event.target.value)} required />
              </div>
            </label>

            <label className="block">
              <span className="label">Senha</span>
              <input className="field" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
            </label>

            {mode === "register" ? (
              <>
                <div>
                  <div className="mb-2 flex justify-between text-xs text-apex-muted">
                    <span>Forca da senha</span>
                    <span>{["fraca", "ok", "boa", "forte"][Math.max(passwordScore - 1, 0)] || "fraca"}</span>
                  </div>
                  <div className="grid grid-cols-4 gap-1">
                    {[1, 2, 3, 4].map((item) => (
                      <div key={item} className={`h-1.5 rounded-full ${passwordScore >= item ? "bg-apex-cyan shadow-glow" : "bg-white/10"}`} />
                    ))}
                  </div>
                </div>
                <label className="block">
                  <span className="label">Confirmar senha</span>
                  <input
                    className={`field ${confirmPassword && confirmPassword !== password ? "border-red-400" : ""}`}
                    type="password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    required
                  />
                </label>
                <label className="block">
                  <span className="label">Tipo de conta</span>
                  <select className="field" value={accountType} onChange={(event) => setAccountType(event.target.value as "admin" | "dev" | "client")}>
                    <option value="client">Cliente / Viewer</option>
                    <option value="dev">Dev</option>
                    <option value="admin">Admin (exige codigo)</option>
                  </select>
                </label>
                {accountType === "admin" ? (
                  <label className="block">
                    <span className="label">Codigo admin opcional</span>
                    <input className="field" value={adminCode} onChange={(event) => setAdminCode(event.target.value)} placeholder="Sem codigo, a conta fica pendente" />
                  </label>
                ) : null}
              </>
            ) : null}

            {error ? <FeedbackBanner type="error" message={error} /> : null}
            {success ? <FeedbackBanner type="success" message={success} /> : null}

            <button className="btn-primary w-full" disabled={loading}>
              {mode === "login" ? <LockKeyhole className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />}
              {loading ? (mode === "login" ? "Autenticando..." : "Criando conta...") : mode === "login" ? "Entrar" : "Criar conta"}
            </button>

            <button
              type="button"
              className="btn-secondary w-full"
              onClick={() => setError("Login com GitHub como provedor de autenticacao esta preparado no design; o OAuth atual conecta repositorios apos login.")}
            >
              <Github className="h-4 w-4" />
              Entrar com GitHub OAuth
            </button>

            <button type="button" className="w-full text-center text-sm text-apex-muted hover:text-apex-cyan" onClick={() => setError("Recuperacao de senha preparada para integracao futura com e-mail transacional.")}>
              Esqueci minha senha
            </button>

            {loading ? (
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-apex-muted">
                  <span>{mode === "login" ? "Inicializando acesso" : "Provisionando conta"}</span>
                  <span>{progress}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-apex-cyan shadow-glow transition-all duration-200" style={{ width: `${progress}%` }} />
                </div>
              </div>
            ) : null}
          </form>
        </section>
      </div>
    </div>
  );
}
