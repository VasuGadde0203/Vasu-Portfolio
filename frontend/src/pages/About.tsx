import { EducationSection } from "../components/EducationSection";
import { Container, SectionHeading, Tag } from "../components/ui";
import { profile } from "../data/profile";
import { usePageMeta } from "../lib/usePageMeta";

export default function About() {
  usePageMeta("About", "Professional background, career journey, current focus, education and courses of Vasu Gadde, Applied AI Engineer.");
  return (
    <Container className="space-y-20 py-16">
      <section>
        <SectionHeading as="h1" eyebrow="About" title="Applied AI, from internship to engineering" />
        <div className="max-w-3xl space-y-4 text-base leading-relaxed text-muted">
          {profile.biography.map((p) => <p key={p}>{p}</p>)}
        </div>
      </section>

      <section>
        <SectionHeading eyebrow="Journey" title="Career journey" />
        <ol className="max-w-3xl space-y-6 border-l border-line pl-6">
          {profile.career_journey.map((j) => (
            <li key={j.label} className="relative">
              <span aria-hidden="true" className="absolute -left-[30px] top-2 h-2 w-2 rounded-full bg-accent" />
              <p className="text-sm text-muted">{j.period}</p>
              <p className="font-display text-lg font-semibold">{j.label}</p>
              <p className="mt-1 text-sm leading-relaxed text-muted">{j.detail}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="grid gap-10 md:grid-cols-2">
        <div>
          <SectionHeading eyebrow="Now" title="Current focus" />
          <p className="text-base leading-relaxed text-muted">{profile.current_focus}</p>
        </div>
        <div>
          <SectionHeading eyebrow="Interests" title="Engineering interests" />
          <ul className="flex flex-wrap gap-2">
            {profile.engineering_interests.map((i) => <li key={i}><Tag>{i}</Tag></li>)}
          </ul>
          <h3 className="mt-8 text-xs font-medium uppercase tracking-wider text-muted">Roles of interest</h3>
          <ul className="mt-3 list-inside list-disc text-sm text-muted">
            {profile.career_interests.roles.map((r) => <li key={r}>{r}</li>)}
          </ul>
        </div>
      </section>

      <section>
        <SectionHeading eyebrow="Learning" title="Education and courses" />
        <EducationSection />
      </section>
    </Container>
  );
}
