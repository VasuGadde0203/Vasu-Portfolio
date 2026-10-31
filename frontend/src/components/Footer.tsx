import { Link } from "react-router-dom";
import { profile } from "../data/profile";
import { Github, Linkedin, Mail } from "./icons";
import { Container } from "./ui";

export function Footer() {
  const { contact } = profile;
  const social = "flex h-9 w-9 items-center justify-center rounded-lg border border-line text-muted hover:-translate-y-0.5 hover:border-accent hover:bg-surface-2 hover:text-accent";
  const heading = "text-[11px] font-semibold uppercase tracking-[0.18em] text-ink";
  const item = "text-sm text-muted hover:text-accent";
  return (
    <footer className="border-t border-line bg-surface/40">
      <Container className="grid gap-10 py-12 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div>
          <p className="flex items-center gap-2.5 font-display text-base font-bold uppercase tracking-wide">
            <span aria-hidden="true" className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-strong text-sm text-on-accent">VG</span>
            {profile.display_name}
          </p>
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted">
            Applied AI engineering: Generative AI, RAG and document intelligence.
          </p>
        </div>
        <nav aria-label="Quick links">
          <p className={heading}>Quick links</p>
          <ul className="mt-4 space-y-2.5">
            <li><Link to="/#about" className={item}>About</Link></li>
            <li><Link to="/#skills" className={item}>Skills</Link></li>
            <li><Link to="/projects" className={item}>Projects</Link></li>
            <li><Link to="/resume" className={item}>Resume</Link></li>
          </ul>
        </nav>
        <nav aria-label="What I do">
          <p className={heading}>What I do</p>
          <ul className="mt-4 space-y-2.5 text-sm text-muted">
            <li>Generative AI &amp; RAG</li>
            <li>Document intelligence</li>
            <li>Workflow automation</li>
            <li>Backend development</li>
          </ul>
        </nav>
        <div>
          <p className={heading}>Find me</p>
          <ul className="mt-4 flex gap-2.5">
            {contact.github && (
              <li><a className={social} href={contact.github} target="_blank" rel="noopener noreferrer" aria-label="GitHub"><Github /></a></li>
            )}
            {contact.linkedin && (
              <li><a className={social} href={contact.linkedin} target="_blank" rel="noopener noreferrer" aria-label="LinkedIn"><Linkedin /></a></li>
            )}
            <li><a className={social} href={`mailto:${contact.email}`} aria-label="Email"><Mail /></a></li>
          </ul>
        </div>
      </Container>
      <div className="border-t border-line py-5">
        <Container>
          <p className="text-xs text-muted">© {new Date().getFullYear()} {profile.name}. All rights reserved.</p>
        </Container>
      </div>
    </footer>
  );
}
