import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { LockKeyhole, Server } from "lucide-react";

import { useAuth } from "../context/AuthContext";

export function Login() {
  const { login, user } = useAuth();
  const [email, setEmail] = useState("admin@apex.local");
  const [password, setPassword] = useState("apex-admin");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid min-h-screen place-items-center px-4 py-8">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center gap-3">
          <div className="grid h-12 w-12 place-items-center rounded-lg border border-apex-purple/70 bg-apex-purple/15 text-apex-cyan">
            <Server className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-white">Apex Host</h1>
            <p className="text-sm text-apex-muted">Painel privado de hospedagem Apex</p>
          </div>
        </div>
        <form className="panel space-y-4 p-5" onSubmit={onSubmit}>
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
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}
