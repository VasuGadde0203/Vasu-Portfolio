import { profile } from "./profile";
import type { SkillLevel } from "../types";

export const skillCategories = profile.skills;
export const skillLevelLabels = profile.skill_levels;

/** Categories shown on the home page (a curated subset; the Skills page shows all). */
export const primarySkillCategories = [
  "Generative AI & LLMs",
  "RAG & Information Retrieval",
  "Document Intelligence & Automation",
  "Backend Development & Databases",
];

export const levelOrder: SkillLevel[] = ["professional", "projects", "familiar", "exploring"];
