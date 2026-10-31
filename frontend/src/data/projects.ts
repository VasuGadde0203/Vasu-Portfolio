import generated from "./generated/projects.json";
import type { Project } from "../types";

// Canonical source: backend/knowledge/projects/*.json. Regenerate with `npm run sync-data`.
export const projects = generated as unknown as Project[];

export const getProject = (id: string | undefined): Project | undefined =>
  projects.find((p) => p.id === id);

export const featuredProjects = projects.filter((p) => p.featured);
