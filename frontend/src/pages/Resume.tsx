import { Container, SectionHeading, Tag, buttonClasses } from "../components/ui";
import { profile } from "../data/profile";
import { usePageMeta } from "../lib/usePageMeta";

export default function Resume() {
  usePageMeta("Resume", "Download the resume of Vasu Gadde, Applied AI Engineer, or read the summary, skills and experience here.");
  const url = profile.contact.resume_url ?? "/Vasu_Resume.pdf";
  return (
    <Container className="py-16">
      <SectionHeading as="h1" eyebrow="Resume" title="Resume" />
      <div className="mb-10 flex flex-wrap gap-3">
        <a href={url} download className={buttonClasses.primary}>Download resume (PDF)</a>
        <a href={url} target="_blank" rel="noopener noreferrer" className={buttonClasses.secondary}>Open in new tab</a>
      </div>

      <div className="grid gap-10 lg:grid-cols-[1fr_1.1fr]">
        <div className="space-y-10">
          <section>
            <h2 className="font-display text-xl font-semibold">Professional summary</h2>
            <p className="mt-3 text-sm leading-relaxed text-muted">{profile.summary}</p>
          </section>
          <section>
            <h2 className="font-display text-xl font-semibold">Skills</h2>
            <dl className="mt-3 space-y-4">
              {profile.skills.map((c) => (
                <div key={c.category}>
                  <dt className="text-sm font-medium">{c.category}</dt>
                  <dd className="mt-1.5 flex flex-wrap gap-1.5">{c.items.map((s) => <Tag key={s.name}>{s.name}</Tag>)}</dd>
                </div>
              ))}
            </dl>
          </section>
          <section>
            <h2 className="font-display text-xl font-semibold">Experience</h2>
            <ul className="mt-3 space-y-5">
              {profile.experience.map((e) => (
                <li key={e.id} className="text-sm">
                  <p className="font-medium">{e.title}, {e.employer}</p>
                  <p className="text-muted">{e.dates} · {e.location}</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
                    {e.responsibilities.map((r) => <li key={r.text}>{r.text}</li>)}
                  </ul>
                </li>
              ))}
            </ul>
          </section>
        </div>
        <section aria-label="Resume preview" className="hidden lg:block">
          <object data={`${url}#toolbar=0`} type="application/pdf" className="sticky top-24 h-[80vh] w-full rounded-xl border border-line bg-surface">
            <p className="p-6 text-sm text-muted">Your browser can't preview the PDF. Use the download button above.</p>
          </object>
        </section>
      </div>
    </Container>
  );
}
