import type { ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { ProjectCard } from "../components/ProjectCard";
import { Container, StatusBadge, Tag } from "../components/ui";
import { profile } from "../data/profile";
import { getProject, projects } from "../data/projects";
import { usePageMeta } from "../lib/usePageMeta";
import NotFound from "./NotFound";

function Block({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-line py-8">
      <h2 className="font-display text-xl font-semibold tracking-tight">{title}</h2>
      <div className="mt-4 max-w-3xl text-sm leading-relaxed text-muted">{children}</div>
    </section>
  );
}

const List = ({ items }: { items: string[] }) => (
  <ul className="space-y-2">
    {items.map((i) => (
      <li key={i} className="flex gap-3">
        <span aria-hidden="true" className="mt-2 h-1 w-1 shrink-0 rounded-full bg-muted" />
        <span>{i}</span>
      </li>
    ))}
  </ul>
);

export default function ProjectDetail() {
  const { projectId } = useParams();
  const project = getProject(projectId);
  usePageMeta(project?.title ?? "Project not found", project?.summary ?? "This project page does not exist.");
  if (!project) return <NotFound />;

  const employer = profile.experience.find((e) => e.id === project.employer);
  const related = project.related_projects.map((id) => projects.find((p) => p.id === id)).filter((p) => p !== undefined);

  return (
    <Container className="py-16">
      <nav aria-label="Breadcrumb" className="mb-6 text-sm text-muted">
        <Link to="/projects" className="hover:text-ink">Projects</Link> <span aria-hidden="true">/</span> {project.title}
      </nav>
      <p className="text-xs uppercase tracking-wider text-accent">{project.category}</p>
      <h1 className="mt-2 max-w-3xl font-display text-4xl font-semibold tracking-tight sm:text-5xl">{project.title}</h1>
      <p className="mt-5 max-w-3xl text-lg leading-relaxed text-muted">{project.summary}</p>
      <ul className="mt-6 flex flex-wrap gap-1.5" aria-label="Technologies">
        {project.technologies.map((t) => <li key={t}><Tag>{t}</Tag></li>)}
      </ul>
      <p className="mt-4 text-sm text-muted">
        {employer ? <>Context: {employer.title} at {employer.employer}. </> : "Employer: not stated in the resume. "}
        {project.confidential && "Confidential details are anonymised; no client names or protected implementation details are published."}
      </p>

      <div className="mt-10">
        <Block title="Overview"><p>{project.overview}</p></Block>
        <Block title="Problem statement"><p>{project.problem}</p></Block>
        <Block title="Technical approach"><List items={project.approach} /></Block>
        <Block title="Architecture">
          <p className="mb-4 text-xs">Badges show whether each point is documented in my resume, general reasoning, or unspecified.</p>
          <ul className="space-y-3">
            {project.architecture.map((a) => (
              <li key={a.label} className="rounded-xl border border-line bg-surface p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-medium text-ink">{a.label}</span>
                  <StatusBadge status={a.status} />
                </div>
                <p className="mt-2">{a.detail}</p>
              </li>
            ))}
          </ul>
        </Block>
        <Block title="Workflow">
          <ol className="space-y-3">
            {project.workflow.map((s, i) => (
              <li key={s.step} className="flex items-start gap-4">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-line text-xs text-ink">{i + 1}</span>
                <span className="flex-1">{s.step}</span>
                <StatusBadge status={s.status} />
              </li>
            ))}
          </ol>
        </Block>
        <Block title="My documented contribution">
          <p className="mb-3 text-ink">{project.contribution.type}</p>
          <List items={project.contribution.items} />
        </Block>
        <Block title="Limitations"><List items={project.limitations} /></Block>
        <Block title="Possible future improvements">
          <p className="mb-3 text-xs">Possible directions only; not completed or planned work.</p>
          <List items={project.future_improvements} />
        </Block>
        <Block title="Related skills">
          <ul className="flex flex-wrap gap-1.5">{project.related_skills.map((s) => <li key={s}><Tag>{s}</Tag></li>)}</ul>
        </Block>
        {project.links.length > 0 && (
          <Block title="Links">
            <ul className="space-y-1">
              {project.links.map((l) => (
                <li key={l.url}><a className="text-accent underline underline-offset-2" href={l.url} target="_blank" rel="noopener noreferrer">{l.label}</a></li>
              ))}
            </ul>
          </Block>
        )}
      </div>

      {related.length > 0 && (
        <section className="mt-6 border-t border-line pt-10">
          <h2 className="font-display text-xl font-semibold tracking-tight">Related projects</h2>
          <div className="mt-6 grid gap-5 md:grid-cols-2">
            {related.map((p) => <ProjectCard key={p.id} project={p} />)}
          </div>
        </section>
      )}
    </Container>
  );
}
