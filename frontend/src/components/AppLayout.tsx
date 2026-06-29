import {
  Activity,
  Boxes,
  Gauge,
  Globe2,
  LayoutDashboard,
  LogOut,
  ScrollText,
  Settings,
  TerminalSquare
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { ApexLogo } from "./ApexLogo";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/projects", label: "Projetos", icon: Boxes },
  { to: "/domains", label: "Dominios", icon: Globe2 },
  { to: "/deploys", label: "Deploys", icon: TerminalSquare },
  { to: "/logs", label: "Logs", icon: ScrollText },
  { to: "/monitoring", label: "Monitoramento", icon: Activity },
  { to: "/settings", label: "Configuracoes", icon: Settings }
];

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="apex-grid min-h-screen bg-apex-bg">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-apex-line/80 bg-[#020713]/90 p-4 shadow-glow backdrop-blur-xl lg:block">
        <div className="mb-8 flex items-center gap-3">
          <ApexLogo className="h-11 w-11" />
          <div>
            <div className="font-semibold text-white">Apex Host</div>
            <div className="text-xs text-apex-muted">Neon cloud deploys</div>
          </div>
        </div>

        <nav className="space-y-1">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition ${
                    isActive ? "border border-apex-cyan/40 bg-apex-cyan/10 text-white shadow-glow" : "text-apex-muted hover:bg-white/5 hover:text-white"
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-apex-line/80 bg-apex-bg/82 backdrop-blur-xl">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6">
            <div className="flex items-center gap-3">
              <ApexLogo className="h-9 w-9 lg:hidden" />
              <div>
                <div className="text-sm font-medium text-white">Apex Technologies</div>
                <div className="text-xs text-apex-muted">Hospedagem privada para projetos Apex</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
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
          <nav className="flex gap-2 overflow-x-auto border-t border-apex-line px-4 py-2 lg:hidden">
            {nav.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    `flex shrink-0 items-center gap-2 rounded-md px-3 py-2 text-xs ${
                      isActive ? "border border-apex-cyan/40 bg-apex-cyan/10 text-white" : "text-apex-muted"
                    }`
                  }
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </header>
        <main className="dashboard-enter mx-auto max-w-7xl px-4 py-6 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
