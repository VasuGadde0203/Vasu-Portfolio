import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import type { Status } from "../types";

export function Container({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`mx-auto w-full max-w-6xl px-5 sm:px-8 ${className}`}>{children}</div>;
}

export function SectionHeading({
  eyebrow,
  title,
  intro,
  as: Tag = "h2",
}: {
  eyebrow?: string;
  title: string;
  intro?: string;
  as?: "h1" | "h2";
}) {
  return (
    <div className="mb-10 max-w-3xl">
      {eyebrow && <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-accent">{eyebrow}</p>}
      <Tag className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">{title}</Tag>
      {intro && <p className="mt-4 text-base leading-relaxed text-muted">{intro}</p>}
    </div>
  );
}

export function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="inline-block rounded-md border border-line bg-surface-2 px-2 py-0.5 text-xs text-muted">
      {children}
    </span>
  );
}

const STATUS_STYLES: Record<Status, { label: string; cls: string }> = {
  documented: { label: "Documented", cls: "border-sage/40 bg-sage/10 text-sage" },
  general: { label: "General reasoning", cls: "border-gold/40 bg-gold/10 text-gold" },
  unspecified: { label: "Unspecified", cls: "border-line text-muted" },
};

export function StatusBadge({ status }: { status: Status }) {
  const s = STATUS_STYLES[status];
  return (
    <span className={`inline-block shrink-0 rounded-full border px-2 py-0.5 text-[11px] ${s.cls}`}>{s.label}</span>
  );
}

const BTN =
  "inline-flex cursor-pointer items-center justify-center gap-2 rounded-full px-6 py-3 text-xs font-semibold uppercase tracking-wider transition-all duration-150 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98]";
export const buttonClasses = {
  primary: `${BTN} bg-accent-strong text-on-accent hover:bg-[#f4a67f] hover:shadow-lg hover:shadow-accent-strong/25`,
  secondary: `${BTN} border border-line bg-surface/60 text-ink hover:border-accent hover:bg-surface-2 hover:text-accent hover:shadow-md hover:shadow-black/20`,
};

export function ButtonLink({
  to,
  href,
  variant = "secondary",
  children,
  download,
}: {
  to?: string;
  href?: string;
  variant?: "primary" | "secondary";
  children: ReactNode;
  download?: boolean;
}) {
  if (to) return <Link to={to} className={buttonClasses[variant]}>{children}</Link>;
  return (
    <a href={href} className={buttonClasses[variant]} download={download}>
      {children}
    </a>
  );
}

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <p role="status" className="py-16 text-center text-sm text-muted">
      {label}
    </p>
  );
}

export function ErrorState({ title = "Something went wrong", message }: { title?: string; message: string }) {
  return (
    <div role="alert" className="rounded-xl border border-red-400/30 bg-red-950/30 p-6">
      <h2 className="font-display text-lg font-semibold">{title}</h2>
      <p className="mt-2 text-sm text-muted">{message}</p>
    </div>
  );
}
