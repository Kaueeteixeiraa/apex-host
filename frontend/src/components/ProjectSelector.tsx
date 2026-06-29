import { Link } from "react-router-dom";

import { Project } from "../lib/api";

export function ProjectSelector({
  projects,
  selectedId,
  onChange
}: {
  projects: Project[];
  selectedId: number | null;
  onChange: (id: number) => void;
}) {
  if (projects.length === 0) {
    return (
      <div className="panel p-5">
        <div className="font-medium text-white">Nenhum projeto cadastrado</div>
        <p className="muted mt-1">Crie um projeto antes de usar esta area.</p>
        <Link className="btn-primary mt-4" to="/projects">
          Criar projeto
        </Link>
      </div>
    );
  }
  return (
    <label className="block">
      <span className="label">Projeto</span>
      <select className="field max-w-md" value={selectedId ?? ""} onChange={(event) => onChange(Number(event.target.value))}>
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
          </option>
        ))}
      </select>
    </label>
  );
}
