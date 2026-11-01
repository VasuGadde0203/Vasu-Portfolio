import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { profile } from "../../data/profile";
import { projects } from "../../data/projects";
import { levelOrder, skillCategories, skillLevelLabels } from "../../data/skills";
import { useChatUi } from "../chat/ChatContext";
import { ContactDetails } from "../ContactSection";
import { ContactForm } from "../ContactForm";
import { EducationSection } from "../EducationSection";
import { ArrowRight, Download, FileText, Server, Sparkle, Workflow } from "../icons";
import { ProjectCard } from "../ProjectCard";
import { ButtonLink, Container, Tag, buttonClasses } from "../ui";

function Section({
  id,
  eyebrow,
  title,
  intro,
  center = false,
  band = false,
  children,
}: {
  id: string;
  eyebrow: string;
  title: string;
  intro?: string;
  center?: boolean;
  band?: boolean;
  children: ReactNode;
}) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className={`scroll-mt-16 border-t border-line py-20 ${band ? "bg-surface/40" : ""}`}>
      <Container>
        <div className={`mb-12 max-w-2xl ${center ? "mx-auto text-center" : ""}`}>
          <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent">{eyebrow}</p>
          <h2 id={`${id}-h`} className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h2>
          {intro && <p className="mt-4 text-base leading-relaxed text-muted">{intro}</p>}
        </div>
        {children}
      </Container>
    </section>
  );
}

/* ---------------------------------------------------------------- About */

export function AboutSection() {
  const c = profile.contact;
  const info = [
    { label: "Name", value: profile.name },
    { label: "Email", value: c.email, href: `mailto:${c.email}` },
    ...(c.show_location && c.location ? [{ label: "Location", value: c.location }] : []),
    { label: "Focus", value: "Generative AI, RAG, document intelligence" },
  ];
  const stats = [
    { value: "2+", label: "Years of combined experience" },
    { value: String(projects.length), label: "Documented projects" },
    { value: String(profile.experience.length), label: "Roles so far" },
    { value: String(skillCategories.length), label: "Skill areas" },
  ];
  return (
    <Section id="about" eyebrow="About me" title="Building practical AI systems that solve real problems">
      <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          {profile.biography.slice(0, 2).map((p) => (
            <p key={p} className="mb-4 text-base leading-relaxed text-muted">{p}</p>
          ))}
          <ul className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {stats.map((s) => (
              <li key={s.label} className="rounded-xl border border-line bg-surface p-4 text-center transition-colors hover:border-accent/60">
                <p className="font-display text-2xl font-semibold text-accent-strong">{s.value}</p>
                <p className="mt-1 text-[11px] leading-snug text-muted">{s.label}</p>
              </li>
            ))}
          </ul>
          <div className="mt-7 flex flex-wrap gap-3">
            <a className={buttonClasses.secondary} href={c.resume_url ?? "/Vasu_Resume.pdf"} download>
              Download resume <Download width={14} height={14} />
            </a>
            <ButtonLink to="/about">More about me</ButtonLink>
          </div>
        </div>
        <dl className="h-fit divide-y divide-line rounded-2xl border border-line bg-surface">
          {info.map((r) => (
            <div key={r.label} className="flex items-baseline gap-5 px-6 py-4">
              <dt className="w-20 shrink-0 text-xs uppercase tracking-wider text-muted">{r.label}</dt>
              <dd className="break-words text-sm">
                {r.href ? <a href={r.href} className="text-accent underline underline-offset-2">{r.value}</a> : r.value}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------- Services */

const SERVICES = [
  { Icon: Sparkle, title: "Generative AI & RAG", text: "Retrieval-augmented chatbots and conversational AI that answer from real business data.", filter: "Generative AI and RAG" },
  { Icon: FileText, title: "Document Intelligence", text: "Hybrid OCR and LLM pipelines that turn invoices and financial PDFs into structured data.", filter: "Document Intelligence" },
  { Icon: Workflow, title: "Workflow Automation", text: "Python automation for payroll reviews, reconciliation and compliance reporting.", filter: "Automation" },
  { Icon: Server, title: "Backend Development", text: "Modular FastAPI services with MongoDB and REST APIs that connect AI to existing systems.", filter: "Backend Development" },
];

export function ServicesSection() {
  return (
    <Section id="services" eyebrow="What I do" title="Where I can help" center band>
      <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {SERVICES.map(({ Icon, title, text, filter }) => (
          <li key={title}>
            <Link
              to={`/projects?category=${encodeURIComponent(filter)}`}
              className="group flex h-full flex-col rounded-2xl border border-line bg-surface p-6 hover:-translate-y-1 hover:border-accent/70 hover:bg-surface-2 hover:shadow-xl hover:shadow-black/25"
            >
              <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-accent/40 bg-accent-strong/10 text-accent">
                <Icon width={24} height={24} />
              </span>
              <h3 className="mt-5 font-display text-lg font-semibold">{title}</h3>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-muted">{text}</p>
              <p className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-accent">
                Related projects <ArrowRight width={13} height={13} className="ml-1 inline transition-transform group-hover:translate-x-1" />
              </p>
            </Link>
          </li>
        ))}
      </ul>
    </Section>
  );
}

/* --------------------------------------------------------------- Skills */

const TILE_NAMES = [
  "Python", "FastAPI", "MongoDB", "PostgreSQL", "Machine Learning", "Deep Learning", "OpenAI API", "GPT-4o", "Qwen2.5", "Pandas", "SQL",
  "Docker", "AWS", "FAISS", "Pinecone", "Surya OCR", "pdfplumber",
];

const monogram = (name: string) => {
  const words = name.split(/[\s-]+/).filter(Boolean);
  return words.length > 1 ? words.map((w) => w[0]).join("").slice(0, 2).toUpperCase() : name.slice(0, 2);
};

export function SkillsSection() {
  const known = new Set(skillCategories.flatMap((c) => c.items.map((s) => s.name)));
  const tiles = TILE_NAMES.filter((n) => known.has(n));
  const byLevel = levelOrder
    .map((level) => ({ level, names: skillCategories.flatMap((c) => c.items.filter((s) => s.level === level).map((s) => s.name)) }))
    .filter((g) => g.names.length > 0 && g.level !== "exploring");
  return (
    <Section id="skills" eyebrow="My expertise" title="Skills & technologies" intro="Grouped by how I have actually used them. The Skills page shows the evidence behind each one.">
      <div className="grid gap-10 lg:grid-cols-[1fr_1fr]">
        <div className="space-y-5">
          {byLevel.map((g) => (
            <div key={g.level} className="rounded-2xl border border-line bg-surface p-5">
              <div className="flex items-baseline justify-between gap-3">
                <h3 className="font-display text-base font-semibold">{skillLevelLabels[g.level]}</h3>
                <span className="text-xs text-accent">{g.names.length} skills</span>
              </div>
              <ul className="mt-3 flex flex-wrap gap-1.5">
                {g.names.slice(0, 12).map((n) => <li key={n}><Tag>{n}</Tag></li>)}
                {g.names.length > 12 && <li><Tag>+{g.names.length - 12} more</Tag></li>}
              </ul>
            </div>
          ))}
          <ButtonLink to="/skills">All skills and evidence <ArrowRight width={14} height={14} /></ButtonLink>
        </div>
        <ul className="grid h-fit grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-3 xl:grid-cols-4">
          {tiles.map((n) => (
            <li key={n} className="flex aspect-square flex-col items-center justify-center gap-2.5 rounded-xl border border-line bg-surface p-2 text-center transition-all hover:-translate-y-1 hover:border-accent/70 hover:bg-surface-2">
              <span aria-hidden="true" className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-strong/15 font-display text-sm font-semibold text-accent">
                {monogram(n)}
              </span>
              <span className="text-xs leading-tight text-muted">{n}</span>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------- Projects */

const HOME_PROJECTS = ["invoice-extraction", "expense-sheet-extraction", "personal-research-assistant"];

export function ProjectsSection() {
  const shown = HOME_PROJECTS.map((id) => projects.find((p) => p.id === id)).filter((p) => p !== undefined);
  return (
    <Section id="projects" eyebrow="Featured projects" title="Some of my recent work" intro="Case studies of documented work. Confidential details are anonymised and no results are claimed beyond what is documented." band>
      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {shown.map((p) => <ProjectCard key={p.id} project={p} />)}
      </div>
      <div className="mt-10 text-center">
        <ButtonLink to="/projects">View all {projects.length} projects <ArrowRight width={14} height={14} /></ButtonLink>
      </div>
    </Section>
  );
}

/* ----------------------------------------------------------- Experience */

export function ExperienceSection() {
  return (
    <Section id="experience" eyebrow="Experience" title="Where I've worked">
      <ul className="grid gap-5 md:grid-cols-2">
        {profile.experience.map((e) => (
          <li key={e.id} className="flex flex-col rounded-2xl border border-line bg-surface p-6 transition-colors hover:border-accent/60">
            <p className="text-xs uppercase tracking-wider text-accent">{e.dates}</p>
            <h3 className="mt-2 font-display text-xl font-semibold">{e.title}</h3>
            <p className="text-sm text-muted">{e.employer} · {e.location}</p>
            <p className="mt-4 flex-1 text-sm leading-relaxed text-muted">{e.summary}</p>
            <ul className="mt-5 flex flex-wrap gap-1.5" aria-label="Technologies">
              {e.technologies.slice(0, 7).map((t) => <li key={t}><Tag>{t}</Tag></li>)}
            </ul>
            <p className="mt-5 text-sm">
              <Link to={`/experience#${e.id}`} className="text-accent underline underline-offset-2">Full responsibilities →</Link>
            </p>
          </li>
        ))}
      </ul>
      <h3 className="mb-6 mt-16 font-display text-xl font-semibold">Education and courses</h3>
      <EducationSection />
    </Section>
  );
}

/* -------------------------------------------------------------- Contact */

export function ContactBlock() {
  const { openChat } = useChatUi();
  return (
    <Section id="contact" eyebrow="Get in touch" title="Let's build something useful together" band>
      <div className="grid gap-8 lg:grid-cols-[0.8fr_1.3fr_0.9fr]">
        <div>
          <p className="text-base leading-relaxed text-muted">
            Have a role or a project in mind? Send a message and I'll reply by email. You can also ask the assistant about my documented experience first.
          </p>
          <button type="button" className={`${buttonClasses.secondary} mt-6`} onClick={() => openChat("How can I contact him?")}>
            <Sparkle width={14} height={14} /> Ask Vasu AI
          </button>
        </div>
        <ContactForm />
        <ContactDetails />
      </div>
    </Section>
  );
}
