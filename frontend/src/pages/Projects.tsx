import { useSearchParams } from "react-router-dom";
import { ProjectCard } from "../components/ProjectCard";
import { Container, SectionHeading } from "../components/ui";
import { filterCategories } from "../data/profile";
import { projects } from "../data/projects";
import { usePageMeta } from "../lib/usePageMeta";

export function filterProjects(category: string | null) {
  return category ? projects.filter((p) => p.filters.includes(category)) : projects;
}

export default function Projects() {
  usePageMeta("Projects", "Case studies of Applied AI projects: document intelligence, RAG chatbots, recruitment automation, backend engineering and workflow automation.");
  const [params, setParams] = useSearchParams();
  const raw = params.get("category");
  const active = raw && (filterCategories as readonly string[]).includes(raw) ? raw : null;
  const shown = filterProjects(active);

  return (
    <Container className="py-16">
      <SectionHeading
        as="h1"
        eyebrow="Projects"
        title="Documented projects"
        intro="Each page separates what is documented from general reasoning and from details that are unspecified. Company-specific details are anonymised."
      />
      <div role="group" aria-label="Filter projects by category" className="mb-8 flex flex-wrap gap-2">
        {["All", ...filterCategories].map((c) => {
          const selected = (c === "All" && !active) || c === active;
          return (
            <button
              key={c}
              type="button"
              aria-pressed={selected}
              onClick={() => setParams(c === "All" ? {} : { category: c })}
              className={`rounded-full border px-4 py-1.5 text-sm transition-colors ${
                selected ? "border-accent bg-accent-strong text-on-accent" : "border-line bg-surface text-muted hover:border-accent hover:bg-surface-2 hover:text-ink"
              }`}
            >
              {c}
            </button>
          );
        })}
      </div>
      <p role="status" className="mb-4 text-sm text-muted">{shown.length} of {projects.length} projects</p>
      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {shown.map((p) => <ProjectCard key={p.id} project={p} />)}
      </div>
    </Container>
  );
}
