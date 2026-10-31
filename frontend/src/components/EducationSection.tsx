import { profile } from "../data/profile";

export function EducationSection() {
  return (
    <div className="grid gap-5 md:grid-cols-2">
      <section className="rounded-2xl border border-line bg-surface p-6" aria-labelledby="edu-h">
        <h3 id="edu-h" className="text-xs font-medium uppercase tracking-wider text-accent">Education</h3>
        {profile.education.map((e) => (
          <div key={e.degree} className="mt-3">
            <p className="font-display text-lg font-semibold">{e.degree}</p>
            <p className="text-sm text-muted">{e.institution}</p>
            <p className="mt-1 text-sm text-muted">{e.dates} · {e.location}</p>
          </div>
        ))}
      </section>
      <section className="rounded-2xl border border-line bg-surface p-6" aria-labelledby="course-h">
        <h3 id="course-h" className="text-xs font-medium uppercase tracking-wider text-accent">Courses &amp; certifications</h3>
        {profile.courses.map((c) => (
          <div key={c.title} className="mt-3">
            <p className="font-display text-lg font-semibold">{c.title}</p>
            <p className="text-sm text-muted">{c.provider} · {c.dates}</p>
            <p className="mt-1 text-xs text-muted">{c.kind}</p>
            <p className="mt-3 text-sm leading-relaxed text-muted">Coverage: {c.coverage.join(", ")}.</p>
          </div>
        ))}
      </section>
    </div>
  );
}
