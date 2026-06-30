import { Link } from "react-router-dom";
import { Compass } from "lucide-react";

import { ApexLogo } from "../components/ApexLogo";

export function NotFound() {
  return (
    <div className="apex-grid grid min-h-screen place-items-center bg-apex-bg px-4">
      <div className="panel max-w-lg p-8 text-center">
        <ApexLogo className="mx-auto mb-5 h-16 w-16" />
        <div className="section-title mb-2">404</div>
        <h1 className="text-3xl font-semibold text-white">Rota fora da orbita</h1>
        <p className="muted mt-3">A pagina solicitada nao existe ou foi movida dentro do Apex Host.</p>
        <Link className="btn-primary mt-6" to="/">
          <Compass className="h-4 w-4" />
          Voltar ao dashboard
        </Link>
      </div>
    </div>
  );
}
