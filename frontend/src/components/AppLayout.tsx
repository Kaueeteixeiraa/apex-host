import {
  Activity,
  Boxes,
  DatabaseBackup,
  Gauge,
  Globe2,
  BookOpen,
  LayoutDashboard,
  LogOut,
  Menu,
  Plus,
  RadioTower,
  ScrollText,
  Server,
  Settings,
  Shield,
  TerminalSquare,
  X
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { api, InfrastructureStatus } from "../lib/api";
import { ApexLogo } from "./ApexLogo";

const nav = [
  { section: "Operacao", to: "/", label: "Dashboard", icon: LayoutDashboard },
  { section: "Operacao", to: "/projects", label: "Projetos", icon: Boxes },
  { section: "Operacao", to: "/domains", label: "Dominios", icon: Globe2 },
  { section: "Operacao", to: "/deploys", label: "Deploys", icon: TerminalSquare },
  { section: "Operacao", to: "/logs", label: "Logs", icon: ScrollText },
  { section: "Infraestrutura", to: "/monitoring", label: "Monitoramento", icon: Activity },
  { section: "Infraestrutura", to: "/infrastructure", label: "Infraestrutura", icon: Server },
  { section: "Infraestrutura", to: "/backups", label: "Backups", icon: DatabaseBackup },
  { section: "Administracao", to: "/help", label: "Ajuda", icon: BookOpen },
  { section: "Administracao", to: "/status", label: "Status", icon: RadioTower },
  { section: "Administracao", to: "/settings", label: "Configuracoes", icon: Settings },
  { section: "Administracao", to: "/admin", label: "Admin", icon: Shield, adminOnly: true }
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [maintenance, setMaintenance] = useState(false);
  const [infra, setInfra] = useState<InfrastructureStatus | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [pageLoading, setPageLoading] = useState(false);

  useEffect(() => {
    void api<{ maintenance_mode: boolean }>("/public/platform")
      .then((data) => setMaintenance(Boolean(data.maintenance_mode)))
      .catch(() => setMaintenance(false));
    void api<InfrastructureStatus>("/monitor/infrastructure")
      .then(setInfra)
      .catch(() => setInfra(null));
  }, []);

  useEffect(() => {
    setPageLoading(true);
    const timeout = window.setTimeout(() => setPageLoading(false), 220);
    return () => window.clearTimeout(timeout);
  }, [location.pathname]);

  const visibleNav = nav.filter((item) => !item.adminOnly || user?.role === "admin");

  if (maintenance && user?.role !== "admin") {
    return (
      <div className="apex-grid grid min-h-screen place-items-center bg-apex-bg px-4">
        <div className="panel max-w-xl p-8 text-center">
          <ApexLogo className="mx-auto mb-5 h-16 w-16" />
          <div className="section-title mb-2">Modo manutencao</div>
          <h1 className="text-3xl font-semibold text-white">Apex Host esta em manutencao programada</h1>
          <p className="muted mt-3">
            O painel esta temporariamente pausado para usuarios comuns. Projetos hospedados continuam independentes dessa tela.
          </p>
          <button className="btn-secondary mt-6" onClick={logout}>
            <LogOut className="h-4 w-4" />
            Sair
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="apex-grid min-h-screen bg-apex-bg">
      {drawerOpen ? <div className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden" onClick={() => setDrawerOpen(false)} /> : null}
      <aside className={`${drawerOpen ? "translate-x-0" : "-translate-x-full"} fixed inset-y-0 left-0 z-40 w-72 border-r border-apex-line/80 bg-[#020713]/95 p-4 shadow-glow backdrop-blur-xl transition-transform lg:hidden`}>
        <SidebarContent visibleNav={visibleNav} collapsed={false} onNavigate={() => setDrawerOpen(false)} onToggle={() => setDrawerOpen(false)} mobile />
      </aside>

      <aside className={`fixed inset-y-0 left-0 z-20 hidden border-r border-apex-line/80 bg-[#020713]/90 p-4 shadow-glow backdrop-blur-xl transition-all lg:block ${collapsed ? "w-20" : "w-64"}`}>
        <SidebarContent visibleNav={visibleNav} collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      </aside>

      <div className={collapsed ? "lg:pl-20" : "lg:pl-64"}>
        <header className="sticky top-0 z-10 border-b border-apex-line/80 bg-apex-bg/82 backdrop-blur-xl">
          {pageLoading ? <div className="absolute inset-x-0 top-0 h-0.5 bg-apex-cyan shadow-glow" /> : null}
          <div className="flex min-h-16 items-center justify-between gap-3 px-4 py-3 sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <button className="btn-secondary shrink-0 p-2 lg:hidden" onClick={() => setDrawerOpen(true)} title="Abrir menu">
                <Menu className="h-4 w-4" />
              </button>
              <ApexLogo size="sm" className="hidden h-9 w-9 shrink-0 sm:block lg:hidden" />
              <div className="min-w-0">
                <div className="text-sm font-medium text-white">Apex Technologies</div>
                <div className="truncate text-xs text-apex-muted">Hospedagem privada para projetos Apex</div>
              </div>
            </div>
            <div className="flex shrink-0 items-center justify-end gap-2 sm:gap-3">
              <HealthPill status={infra?.overall_status || "stable"} />
              <div className="hidden rounded-full border border-apex-line bg-white/5 px-3 py-1 text-xs text-apex-muted md:block" title="Rodando no ambiente local desta maquina.">
                {labelEnvironment(infra)}
              </div>
              {infra?.dry_run ? (
                <div className="rounded-full border border-yellow-400/40 bg-yellow-400/10 px-3 py-1 text-xs font-semibold text-yellow-100" title="Deploys reais com Docker estao desativados neste ambiente.">
                  DRY RUN ATIVO
                </div>
              ) : null}
              <NavLink className="btn-secondary hidden sm:inline-flex" to="/logs">
                <ScrollText className="h-4 w-4" />
                <span className="hidden md:inline">Logs</span>
              </NavLink>
              {location.pathname !== "/projects/new" ? (
              <NavLink className="btn-primary hidden sm:inline-flex" to="/projects/new">
                <Plus className="h-4 w-4" />
                <span className="hidden md:inline">Novo projeto</span>
              </NavLink>
              ) : null}
              <div className="hidden items-center gap-2 rounded-full border border-apex-line bg-white/5 px-3 py-1 text-xs text-apex-muted sm:flex">
                <Gauge className="h-3.5 w-3.5 text-apex-cyan" />
                {user?.email}
              </div>
              <button className="btn-secondary" onClick={logout} title="Sair">
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sair</span>
              </button>
            </div>
          </div>
        </header>
        <main className="dashboard-enter mx-auto max-w-7xl px-4 py-6 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function SidebarContent({
  visibleNav,
  collapsed,
  mobile,
  onNavigate,
  onToggle
}: {
  visibleNav: typeof nav;
  collapsed: boolean;
  mobile?: boolean;
  onNavigate?: () => void;
  onToggle: () => void;
}) {
  let lastSection = "";
  return (
    <>
      <div className={collapsed ? "mb-8 flex flex-col items-center gap-3" : "mb-8 flex items-center justify-between gap-3"}>
        <div className={collapsed ? "grid w-full place-items-center" : "min-w-0"}>
          <ApexLogo size="md" collapsed={collapsed} showText />
        </div>
        <button className="btn-secondary shrink-0 p-2" onClick={onToggle} title={mobile ? "Fechar menu" : collapsed ? "Expandir menu" : "Recolher menu"}>
          {mobile ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      </div>

      <nav className="space-y-1">
        {visibleNav.map((item) => {
          const Icon = item.icon;
          const showSection = item.section !== lastSection;
          lastSection = item.section;
          return (
            <div key={item.to}>
              {showSection && !collapsed ? <div className="mb-2 mt-5 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-apex-muted/70">{item.section}</div> : null}
              <NavLink
                to={item.to}
                end={item.to === "/"}
                onClick={onNavigate}
                className={({ isActive }) =>
                  `flex h-10 items-center ${collapsed ? "justify-center px-0" : "gap-3 px-3"} rounded-md border py-2 text-sm transition duration-200 ${
                    isActive
                      ? "border-apex-cyan/50 bg-apex-cyan/10 text-white shadow-glow"
                      : "border-transparent text-apex-muted hover:border-apex-line hover:bg-white/5 hover:text-white"
                  }`
                }
                title={collapsed ? item.label : undefined}
              >
                <Icon className="h-4 w-4" />
                {!collapsed ? item.label : null}
              </NavLink>
            </div>
          );
        })}
      </nav>
    </>
  );
}

function labelEnvironment(infra?: InfrastructureStatus | null) {
  if (infra?.dry_run) return "Dry Run";
  const stage = (infra?.deploy_stage || "").toLowerCase().replace("_", "-");
  if (stage === "staging-vps" || stage === "staging") return "Staging VPS";
  if (stage === "production" || infra?.environment === "production") return "Producao";
  if (!infra?.environment || infra.environment === "development") return "Local";
  return infra.environment;
}

function HealthPill({ status }: { status: string }) {
  const tone =
    status === "critical"
      ? "border-red-400/40 bg-red-500/10 text-red-100"
      : status === "attention"
        ? "border-yellow-400/40 bg-yellow-400/10 text-yellow-100"
        : "border-emerald-400/40 bg-emerald-400/10 text-emerald-100";
  const label = status === "critical" ? "Critico" : status === "attention" ? "Atencao" : "Estavel";
  return (
    <div className={`hidden items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium sm:flex ${tone}`} title={label === "Estavel" ? "Todos os servicos principais estao estaveis." : "Ha alertas ou servicos exigindo atencao no monitoramento."}>
      <span className="h-2 w-2 rounded-full bg-current apex-pulse" />
      {label}
    </div>
  );
}
