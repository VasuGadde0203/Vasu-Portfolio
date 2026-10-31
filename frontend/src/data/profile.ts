import generated from "./generated/profile.json";
import type { Profile } from "../types";

// Canonical source: backend/knowledge/profile.json. Regenerate with `npm run sync-data`.
export const profile = generated as unknown as Profile;

export const filterCategories = [
  "Applied AI",
  "Generative AI and RAG",
  "Document Intelligence",
  "Automation",
  "Backend Development",
  "Data Processing",
] as const;
