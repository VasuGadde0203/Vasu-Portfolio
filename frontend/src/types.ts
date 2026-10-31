// Mirrors backend/app/schemas/content.py. The data itself is generated from the backend knowledge files.
export type SkillLevel = "professional" | "projects" | "familiar" | "exploring";
export type Status = "documented" | "general" | "unspecified";

export interface Contact {
  email: string;
  phone: string | null;
  show_phone: boolean;
  location: string | null;
  show_location: boolean;
  linkedin: string | null;
  github: string | null;
  resume_url: string | null;
}

export interface Responsibility {
  verb: string;
  text: string;
  projects: string[];
}

export interface Experience {
  id: string;
  employer: string;
  title: string;
  start: string;
  end: string;
  dates: string;
  location: string;
  summary: string;
  responsibilities: Responsibility[];
  technologies: string[];
  related_projects: string[];
  related_projects_note?: string | null;
}

export interface Education {
  degree: string;
  short: string;
  institution: string;
  dates: string;
  location: string;
}

export interface Course {
  title: string;
  provider: string;
  dates: string;
  kind: string;
  coverage: string[];
}

export interface Skill {
  name: string;
  level: SkillLevel;
  evidence: string;
}

export interface SkillCategory {
  category: string;
  items: Skill[];
}

export interface Profile {
  name: string;
  display_name: string;
  title: string;
  headline: string;
  tagline: string;
  summary: string;
  contact: Contact;
  proof_points: string[];
  biography: string[];
  career_journey: { period: string; label: string; detail: string }[];
  current_focus: string;
  engineering_interests: string[];
  career_interests: { roles: string[]; note: string };
  experience: Experience[];
  education: Education[];
  courses: Course[];
  skill_levels: Record<SkillLevel, string>;
  skills: SkillCategory[];
}

export interface Project {
  id: string;
  title: string;
  category: string;
  filters: string[];
  featured: boolean;
  employer: string | null;
  confidential: boolean;
  summary: string;
  technologies: string[];
  overview: string;
  problem: string;
  approach: string[];
  architecture: { label: string; detail: string; status: Status }[];
  workflow: { step: string; status: Status }[];
  contribution: { type: string; items: string[] };
  limitations: string[];
  future_improvements: string[];
  related_skills: string[];
  related_projects: string[];
  links: { label: string; url: string }[];
}

export interface Source {
  document_id: string;
  title: string;
  section: string | null;
  project_id: string | null;
  url: string | null;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  project_ids: string[];
  evidence: "strong" | "partial" | "none";
}
