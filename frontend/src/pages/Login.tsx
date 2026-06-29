import { FormEvent, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { LockKeyhole } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { ApexLogo } from "../components/ApexLogo";

export function Login() {
  const { login, user } = useAuth();
  const [email, setEmail] = useState("admin@apex.local");
  const [password, setPassword] = useState("apex-admin");
  const [error, setError] = useState<string | null>(null);
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

  if (user && !loading) return <Navigate to="/" replace />;
  if (user && redirect) return <Navigate to="/" replace />;

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setProgress(12);
    setError(null);
    try {
      await login(email, password);
      setProgress(100);
      window.setTimeout(() => setRedirect(true), 420);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no login");
      setProgress(0);
      setLoading(false);
    }
  };

  return (
    <div className="apex-grid relative grid min-h-screen place-items-center overflow-hidden px-4 py-8">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(24,182,255,0.16),transparent_34rem)]" />
      <div className="w-full max-w-md">
        <div className="relative z-10 mb-6 flex flex-col items-center text-center">
          <div className="relative grid h-28 w-28 place-items-center">
            {loading ? (
              <div className="energy-ring absolute inset-0 rounded-full border border-apex-cyan/30 border-t-apex-cyan shadow-glow" />
            ) : null}
            <ApexLogo className="h-24 w-24" animated={loading} />
          </div>
          <div>
            <h1 className="mt-3 text-4xl font-semibold tracking-[0.18em] text-white">APEX HOST</h1>
            <p className="text-sm text-apex-muted">Painel privado de hospedagem Apex</p>
          </div>
        </div>
        <form className="panel relative z-10 space-y-4 p-5" onSubmit={onSubmit}>
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>
            <input id="email" className="field" value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="password">
              Senha
            </label>
            <input
              id="password"
              className="field"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          {error ? <div className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{error}</div> : null}
          <button className="btn-primary w-full" disabled={loading}>
            <LockKeyhole className="h-4 w-4" />
            {loading ? "Autenticando..." : "Entrar"}
          </button>
          {loading ? (
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-apex-muted">
                <span>Inicializando acesso</span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-white/10">
                <div className="h-full rounded-full bg-apex-cyan shadow-glow transition-all duration-200" style={{ width: `${progress}%` }} />
              </div>
            </div>
          ) : null}
        </form>
      </div>
    </div>
  );
}
