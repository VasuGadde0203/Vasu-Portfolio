import { Link } from "react-router-dom";
import { getProject } from "../data/projects";
import type { Experience } from "../types";
import { Tag } from "./ui";

export function ExperienceTimeline({ entries, detailed = true }: { entries: Experience[]; detailed?: boolean }) {
  return (
    <ol className="relative space-y-12 border-l border-line pl-6 sm:pl-10">
      {entries.map((e) => (
        <li key={e.id} id={e.id} className="relative scroll-mt-24">
          <span aria-hidden="true" className="absolute -left-[30px] top-2 h-2.5 w-2.5 rounded-full bg-accent sm:-left-[46px]" />
          <p className="text-sm text-muted">
            {e.dates} · {e.location}
          </p>
          <h3 className="mt-1 font-display text-2xl font-semibold tracking-tight">{e.title}</h3>
          <p className="text-base text-accent">{e.employer}</p>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">{e.summary}</p>

          {detailed ? (
            <>
              <h4 className="mt-6 text-xs font-medium uppercase tracking-wider text-muted">Responsibilities</h4>
              <ul className="mt-3 max-w-3xl space-y-3">
                {e.responsibilities.map((r) => (
                  <li key={r.text} className="flex gap-3 text-sm leading-relaxed">
                    <span aria-hidden="true" className="mt-2 h-1 w-1 shrink-0 rounded-full bg-muted" />
                    <span>
                      {r.text}
                      {r.projects.map((pid) => {
                        const p = getProject(pid);
                        return p ? (
                          <Link key={pid} to={`/projects/${pid}`} className="ml-2 whitespace-nowrap text-xs text-accent underline underline-offset-2">
                            Case study
                          </Link>
                        ) : null;
                      })}
                    </span>
                  </li>
                ))}
              </ul>

              <h4 className="mt-6 text-xs font-medium uppercase tracking-wider text-muted">Technologies</h4>
              <ul className="mt-3 flex flex-wrap gap-1.5">
                {e.technologies.map((t) => (
                  <li key={t}>
                    <Tag>{t}</Tag>
                  </li>
                ))}
              </ul>

              <h4 className="mt-6 text-xs font-medium uppercase tracking-wider text-muted">Related projects</h4>
              <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                {e.related_projects.map((pid) => {
                  const p = getProject(pid);
                  return p ? (
                    <li key={pid}>
                      <Link to={`/projects/${pid}`} className="text-accent underline underline-offset-2">
                        {p.title}
                      </Link>
                    </li>
                  ) : null;
                })}
              </ul>
              {e.related_projects_note && <p className="mt-2 max-w-3xl text-xs text-muted">{e.related_projects_note}</p>}
            </>
          ) : (
            <p className="mt-3 text-sm">
              <Link to={`/experience#${e.id}`} className="text-accent underline underline-offset-2">
                Full responsibilities →
              </Link>
            </p>
          )}
        </li>
      ))}
    </ol>
  );
}
