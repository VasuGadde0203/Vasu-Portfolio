import { profile } from "../data/profile";
import { buttonClasses } from "./ui";

export function ContactDetails() {
  const c = profile.contact;
  const rows: { label: string; node: React.ReactNode }[] = [
    { label: "Email", node: <a className="text-accent underline underline-offset-2" href={`mailto:${c.email}`}>{c.email}</a> },
  ];
  if (c.show_phone && c.phone) {
    rows.push({ label: "Phone", node: <a className="text-accent underline underline-offset-2" href={`tel:${c.phone}`}>{c.phone}</a> });
  }
  if (c.linkedin) {
    rows.push({ label: "LinkedIn", node: <a className="text-accent underline underline-offset-2" href={c.linkedin} target="_blank" rel="noopener noreferrer">{c.linkedin.replace(/^https?:\/\//, "")}</a> });
  }
  if (c.github) {
    rows.push({ label: "GitHub", node: <a className="text-accent underline underline-offset-2" href={c.github} target="_blank" rel="noopener noreferrer">{c.github.replace(/^https?:\/\//, "")}</a> });
  }
  if (c.show_location && c.location) rows.push({ label: "Location", node: <span>{c.location}</span> });
  return (
    <dl className="divide-y divide-line rounded-2xl border border-line bg-surface">
      {rows.map((r) => (
        <div key={r.label} className="flex flex-col gap-1 px-6 py-4 sm:flex-row sm:items-baseline sm:gap-6">
          <dt className="w-24 shrink-0 text-xs uppercase tracking-wider text-muted">{r.label}</dt>
          <dd className="break-all text-sm sm:break-normal">{r.node}</dd>
        </div>
      ))}
    </dl>
  );
}

export function EmailButton() {
  return (
    <a className={buttonClasses.secondary} href={`mailto:${profile.contact.email}`}>
      Email me
    </a>
  );
}
