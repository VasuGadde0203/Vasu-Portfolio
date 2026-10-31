import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { profile } from "../data/profile";
import { Container, buttonClasses } from "./ui";

const LINKS = [
  { id: "home", label: "Home" },
  { id: "about", label: "About" },
  { id: "services", label: "What I do" },
  { id: "skills", label: "Skills" },
  { id: "projects", label: "Projects" },
  { id: "experience", label: "Experience" },
  { id: "contact", label: "Contact" },
];

/** Which section the visitor is in: scroll position on the home page, otherwise the route. */
function useActiveId(): string {
  const { pathname } = useLocation();
  const [active, setActive] = useState("home");

  useEffect(() => {
    if (pathname !== "/") {
      const seg = pathname.split("/")[1];
      setActive(LINKS.some((l) => l.id === seg) ? seg : "");
      return;
    }
    setActive("home");
    const els = LINKS.map((l) => document.getElementById(l.id)).filter((e): e is HTMLElement => !!e);
    const obs = new IntersectionObserver(
      (entries) => {
        const hit = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (hit) setActive(hit.target.id);
      },
      { rootMargin: "-30% 0px -55% 0px", threshold: [0, 0.25, 0.5, 1] },
    );
    els.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, [pathname]);

  return active;
}

export function Navbar() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  const active = useActiveId();
  useEffect(() => setOpen(false), [pathname]);

  const link = (id: string) =>
    `relative rounded-md px-3 py-2 text-[11px] font-semibold uppercase tracking-wider transition-colors hover:bg-surface-2 hover:text-ink ${
      active === id ? "text-accent" : "text-muted"
    } ${active === id ? "after:absolute after:inset-x-3 after:-bottom-px after:h-0.5 after:rounded-full after:bg-accent-strong" : ""}`;
  const to = (id: string) => (id === "home" ? "/" : `/#${id}`);

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg/90 backdrop-blur">
      <Container className="flex h-16 items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-2.5 font-display text-base font-bold uppercase tracking-wide">
          <span aria-hidden="true" className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-strong text-sm text-on-accent">VG</span>
          <span>
            {profile.display_name.split(" ")[0]} <span className="text-accent-strong">{profile.display_name.split(" ").slice(1).join(" ")}</span>
          </span>
        </Link>
        <nav aria-label="Primary" className="hidden items-center gap-0.5 lg:flex">
          {LINKS.map((l) => (
            <Link key={l.id} to={to(l.id)} className={link(l.id)} aria-current={active === l.id ? "location" : undefined}>
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <Link to="/#contact" className={`${buttonClasses.secondary} hidden !border-accent-strong/70 !px-5 !py-2 text-accent sm:inline-flex`}>
            Let's talk
          </Link>
          <button
            type="button"
            className="rounded-md border border-line px-3 py-1.5 text-sm hover:border-accent hover:bg-surface-2 hover:text-accent lg:hidden"
            aria-expanded={open}
            aria-controls="mobile-nav"
            onClick={() => setOpen((o) => !o)}
          >
            {open ? "Close" : "Menu"}
          </button>
        </div>
      </Container>
      {open && (
        <nav id="mobile-nav" aria-label="Primary mobile" className="border-t border-line lg:hidden">
          <Container className="flex flex-col py-2">
            {LINKS.map((l) => (
              <Link key={l.id} to={to(l.id)} className={link(l.id)}>
                {l.label}
              </Link>
            ))}
          </Container>
        </nav>
      )}
    </header>
  );
}
