import { Link } from "react-router-dom";
import type { Project } from "../types";
import { FileText, Github, Server, Sparkle, Workflow } from "./icons";
import { Tag } from "./ui";

// Projects have no screenshots, so each card gets a generated banner keyed to its main category.
function bannerIcon(project: Project) {
  const f = project.filters[0] ?? "";
  if (f.includes("Document")) return FileText;
  if (f.includes("Automation")) return Workflow;
  if (f.includes("Backend")) return Server;
  return Sparkle;
}

export function ProjectCard({ project }: { project: Project }) {
  const Icon = bannerIcon(project);
  const github = project.links.find((l) => l.url.startsWith("https://github.com/"));
  return (
    <article className="group relative flex h-full flex-col overflow-hidden rounded-2xl border border-line bg-surface transition-all hover:-translate-y-1 hover:border-accent/60 hover:shadow-xl hover:shadow-black/25">
      <div aria-hidden="true" className="relative flex h-28 items-center justify-center overflow-hidden border-b border-line bg-gradient-to-br from-accent-strong/25 via-surface-2 to-surface">
        <div className="dot-grid absolute inset-0 opacity-70" />
        <span className="relative flex h-14 w-14 items-center justify-center rounded-2xl border border-accent/50 bg-bg/60 text-accent transition-transform group-hover:scale-110">
          <Icon width={26} height={26} />
        </span>
      </div>
      <div className="flex flex-1 flex-col p-6">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-accent">{project.category}</p>
        <h3 className="mt-2 font-display text-xl font-semibold tracking-tight">
          <Link
            to={`/projects/${project.id}`}
            className="after:absolute after:inset-0 after:content-[''] focus-visible:after:rounded-2xl"
          >
            {project.title}
          </Link>
        </h3>
        <p className="mt-3 flex-1 text-sm leading-relaxed text-muted">{project.summary}</p>
        <ul className="mt-5 flex flex-wrap gap-1.5" aria-label="Technologies">
          {project.technologies.map((t) => (
            <li key={t}>
              <Tag>{t}</Tag>
            </li>
          ))}
        </ul>
        <div className="mt-5 flex items-center justify-between gap-3">
          <p className="text-sm text-ink">
            Read case study <span aria-hidden="true" className="inline-block transition-transform group-hover:translate-x-1">→</span>
          </p>
          {github && (
            <a
              href={github.url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`${project.title} on GitHub`}
              className="relative z-10 inline-flex items-center gap-1.5 rounded-full border border-line px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted hover:border-accent hover:bg-surface-2 hover:text-accent"
            >
              <Github width={14} height={14} /> GitHub
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
