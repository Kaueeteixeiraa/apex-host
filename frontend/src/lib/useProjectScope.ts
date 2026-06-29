import { useEffect, useMemo, useState } from "react";

import { api, Project } from "./api";

export function useProjectScope(routeProjectId?: string) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(routeProjectId ? Number(routeProjectId) : null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const items = await api<Project[]>("/projects");
      setProjects(items);
      if (routeProjectId) setSelectedId(Number(routeProjectId));
      else if (!selectedId && items[0]) setSelectedId(items[0].id);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar projetos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadProjects();
  }, [routeProjectId]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedId) || null,
    [projects, selectedId]
  );

  return { projects, selectedId, selectedProject, setSelectedId, loading, error, reloadProjects: loadProjects };
}
