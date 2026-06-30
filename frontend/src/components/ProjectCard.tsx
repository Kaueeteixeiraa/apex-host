import { ExternalLink, GitBranch, Rocket, Settings } from "lucide-react";
import { Link } from "react-router-dom";

import { formatDate, Project } from "../lib/api";
import { StatusBadge } from "./StatusBadge";

export function ProjectCard({ project, onDeploy }: { project: Project; onDeploy?: (project: Project) => void }) {
  const url = project.primary_domain || project.auto_subdomain;

  return (
    <article className="panel group relative overflow-hidden p-4 hover:-translate-y-1 hover:border-apex-cyan/70">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-apex-cyan to-transparent opacity-60" />
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to={`/projects/${project.id}`} className="text-lg font-semibold text-white hover:text-apex-cyan">
            {project.name}
          </Link>
          <div className="mt-1 flex items-center gap-2 text-xs text-apex-muted">
            <GitBranch className="h-3.5 w-3.5" />
            {project.branch}
          </div>
        </div>
        <StatusBadge status={project.status} />
      </div>
      <div className="mt-4 rounded-md border border-apex-line bg-black/20 p-3">
        <div className="text-xs text-apex-muted">Dominio principal</div>
        <div className="mt-1 truncate text-sm text-apex-text">{url}</div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
        <div>
          <div className="text-apex-muted">Framework</div>
          <div className="mt-1 text-white">{project.project_type}</div>
        </div>
        <div>
          <div className="text-apex-muted">Ultimo deploy</div>
          <div className="mt-1 text-white">{formatDate(project.last_deploy_at)}</div>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <a className="btn-secondary flex-1" href={`https://${url}`} target="_blank" rel="noreferrer">
          <ExternalLink className="h-4 w-4" />
          Acessar
        </a>
        <button className="btn-primary flex-1" onClick={() => onDeploy?.(project)}>
          <Rocket className="h-4 w-4" />
          Deploy
        </button>
        <Link className="btn-secondary" to={`/projects/${project.id}`}>
          <Settings className="h-4 w-4" />
        </Link>
      </div>
    </article>
  );
}
