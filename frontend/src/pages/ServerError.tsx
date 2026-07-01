import { Link } from "react-router-dom";
import { RefreshCcw, ServerCrash } from "lucide-react";

import { ApexLogo } from "../components/ApexLogo";

export function ServerError() {
  return (
    <div className="apex-grid grid min-h-screen place-items-center bg-apex-bg px-4">
      <div className="panel max-w-lg p-8 text-center">
        <ApexLogo className="mx-auto mb-5 h-16 w-16" />
        <div className="section-title mb-2">500</div>
        <h1 className="text-3xl font-semibold text-white">Falha operacional detectada</h1>
        <p className="muted mt-3">O painel encontrou um erro interno. Verifique logs, worker e backend antes de tentar novamente.</p>
        <div className="mt-6 flex flex-col justify-center gap-2 sm:flex-row">
          <button className="btn-secondary" onClick={() => window.location.reload()}>
            <RefreshCcw className="h-4 w-4" />
            Recarregar
          </button>
          <Link className="btn-primary" to="/logs">
            <ServerCrash className="h-4 w-4" />
            Ver logs
          </Link>
        </div>
      </div>
    </div>
  );
}
