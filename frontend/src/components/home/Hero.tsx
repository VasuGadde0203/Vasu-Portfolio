import { profile } from "../../data/profile";
import { useChatUi } from "../chat/ChatContext";
import { ArrowRight, Github, Linkedin, Mail, MapPin, Sparkle } from "../icons";
import { ButtonLink, Container, buttonClasses } from "../ui";

const STEPS = [
  { label: "Verified knowledge", detail: "Resume-derived profile and project case studies" },
  { label: "Embeddings", detail: "Each section turned into a vector" },
  { label: "Vector search", detail: "PostgreSQL + pgvector finds the best matches" },
  { label: "Grounded answer", detail: "The LLM answers only from what was retrieved" },
];

const CHIPS = [
  { label: "Python", cls: "left-[2%] top-[14%]", delay: "0s" },
  { label: "FastAPI", cls: "right-[0%] top-[8%]", delay: "-1.2s" },
  { label: "GPT-4o", cls: "right-[-2%] top-[54%]", delay: "-2.4s" },
  { label: "RAG", cls: "left-[-2%] top-[60%]", delay: "-3.1s" },
  { label: "OCR", cls: "right-[10%] bottom-[2%]", delay: "-0.6s" },
  { label: "MongoDB", cls: "left-[8%] bottom-[0%]", delay: "-1.9s" },
];

function HeroVisual() {
  const { openChat } = useChatUi();
  return (
    // Large screens: a square stage with rings and floating chips around a centred card.
    // Phones and tablets: the same content as a normal stacked block (a row of chips, then the card), so nothing overflows.
    <div className="relative mx-auto w-full max-w-[480px] lg:aspect-square" aria-label="Diagram of the Ask Vasu AI retrieval pipeline" role="group">
      <div aria-hidden="true" className="absolute inset-0 rounded-3xl bg-accent-strong/10 blur-3xl lg:inset-[16%] lg:rounded-full lg:bg-accent-strong/15" />
      <div aria-hidden="true" className="absolute inset-[3%] hidden rounded-full border border-line/70 lg:block" />
      <div aria-hidden="true" className="absolute inset-[12%] hidden rounded-full border border-dashed border-line/60 lg:block" />
      <div aria-hidden="true" className="orbit-arc absolute inset-[3%] hidden rounded-full lg:block" />

      <ul aria-hidden="true" className="relative mb-4 flex flex-wrap justify-center gap-2 lg:hidden">
        {CHIPS.map((c) => (
          <li key={c.label} className="glass flex items-center gap-2 rounded-xl border border-line px-3 py-1.5 text-xs font-medium">
            <span className="h-2 w-2 rounded-full bg-accent-strong" />
            {c.label}
          </li>
        ))}
      </ul>
      {CHIPS.map((c) => (
        <span
          key={c.label}
          aria-hidden="true"
          style={{ animationDelay: c.delay }}
          className={`float-chip glass absolute ${c.cls} hidden items-center gap-2 rounded-xl border border-line px-3 py-2 text-xs font-medium shadow-lg shadow-black/30 lg:flex`}
        >
          <span className="h-2 w-2 rounded-full bg-accent-strong" />
          {c.label}
        </span>
      ))}

      <div className="glass relative rounded-2xl border border-line p-4 shadow-2xl shadow-black/40 sm:p-5 lg:absolute lg:inset-x-[11%] lg:top-1/2 lg:-translate-y-1/2">
        <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-accent">
          <Sparkle width={14} height={14} /> Ask Vasu AI
        </p>
        <ol className="mt-3 space-y-0">
          {STEPS.map((s, i) => (
            <li key={s.label} className="relative flex gap-3 pb-3 last:pb-0">
              {i < STEPS.length - 1 && <span aria-hidden="true" className="absolute left-[9px] top-5 h-full w-px bg-line" />}
              <span aria-hidden="true" className="relative z-10 mt-0.5 flex h-[19px] w-[19px] shrink-0 items-center justify-center rounded-full border border-accent/70 bg-bg text-[10px] font-semibold text-accent">
                {i + 1}
              </span>
              <div>
                <p className="text-sm font-medium leading-tight">{s.label}</p>
                <p className="mt-0.5 text-[11px] leading-snug text-muted">{s.detail}</p>
              </div>
            </li>
          ))}
        </ol>
        <button type="button" onClick={() => openChat()} className={`${buttonClasses.primary} mt-4 w-full !py-2.5`}>
          Try it live <ArrowRight width={14} height={14} />
        </button>
      </div>
    </div>
  );
}

export function Hero() {
  const { contact } = profile;
  const [first, ...rest] = profile.display_name.split(" ");
  const social = "flex h-10 w-10 items-center justify-center rounded-lg border border-line bg-surface/60 text-muted hover:-translate-y-0.5 hover:border-accent hover:bg-surface-2 hover:text-accent";
  return (
    <section id="home" className="relative overflow-hidden scroll-mt-16">
      <div aria-hidden="true" className="dot-grid absolute inset-0" />
      <Container className="relative grid items-center gap-12 py-16 sm:py-24 lg:grid-cols-[1.05fr_0.95fr]">
        <div>
          <p className="fade-up text-[11px] font-semibold uppercase tracking-[0.22em] text-accent">Hello, I'm</p>
          <h1 className="fade-up mt-4 font-display text-6xl font-bold leading-[0.95] tracking-tight sm:text-7xl lg:text-8xl">
            {first} <span className="text-accent-strong">{rest.join(" ")}</span>
          </h1>
          <p className="fade-up mt-5 font-display text-2xl text-ink sm:text-3xl">
            Applied AI Engineer<span aria-hidden="true" className="caret ml-1 text-accent-strong">|</span>
          </p>
          <p className="fade-up mt-5 max-w-xl text-base leading-relaxed text-muted">{profile.tagline}</p>
          <div className="fade-up mt-8 flex flex-wrap gap-3">
            <ButtonLink to="/#contact" variant="primary">Hire me <ArrowRight width={14} height={14} /></ButtonLink>
            <ButtonLink to="/#projects">View my work <ArrowRight width={14} height={14} /></ButtonLink>
          </div>
          <div className="fade-up mt-8 flex flex-wrap items-center gap-x-6 gap-y-4">
            <ul className="flex gap-2.5">
              {contact.github && (
                <li><a className={social} href={contact.github} target="_blank" rel="noopener noreferrer" aria-label="GitHub"><Github /></a></li>
              )}
              {contact.linkedin && (
                <li><a className={social} href={contact.linkedin} target="_blank" rel="noopener noreferrer" aria-label="LinkedIn"><Linkedin /></a></li>
              )}
              <li><a className={social} href={`mailto:${contact.email}`} aria-label="Email"><Mail /></a></li>
            </ul>
            {contact.show_location && contact.location && (
              <p className="flex items-center gap-2 text-sm text-muted">
                <MapPin width={16} height={16} className="text-accent" /> Based in {contact.location}
              </p>
            )}
          </div>
        </div>
        <HeroVisual />
      </Container>
    </section>
  );
}
