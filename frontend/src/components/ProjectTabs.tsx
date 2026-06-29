import { NavLink } from "react-router-dom";

const tabs = [
  { to: "", label: "Resumo", end: true },
  { to: "deploys", label: "Deploys" },
  { to: "logs", label: "Logs" },
  { to: "domains", label: "Dominios" },
  { to: "env", label: "Variaveis" },
  { to: "monitoring", label: "Monitoramento" }
];

export function ProjectTabs({ projectId }: { projectId: number }) {
  return (
    <div className="mb-5 flex gap-2 overflow-x-auto border-b border-apex-line pb-2">
      {tabs.map((tab) => (
        <NavLink
          key={tab.label}
          to={`/projects/${projectId}/${tab.to}`.replace(/\/$/, "")}
          end={tab.end}
          className={({ isActive }) =>
            `shrink-0 rounded-md px-3 py-2 text-sm ${
              isActive ? "border border-apex-cyan/40 bg-apex-cyan/10 text-white" : "text-apex-muted hover:bg-white/5 hover:text-white"
            }`
          }
        >
          {tab.label}
        </NavLink>
      ))}
    </div>
  );
}
