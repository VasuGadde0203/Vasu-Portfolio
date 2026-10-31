import { skillLevelLabels } from "../data/skills";
import type { SkillCategory } from "../types";
import { Tag } from "./ui";

export function SkillsGrid({ categories, showEvidence = false }: { categories: SkillCategory[]; showEvidence?: boolean }) {
  return (
    <div className="grid gap-5 md:grid-cols-2">
      {categories.map((c) => (
        <section key={c.category} className="rounded-2xl border border-line bg-surface p-6">
          <h3 className="font-display text-lg font-semibold">{c.category}</h3>
          {showEvidence ? (
            <ul className="mt-4 space-y-3">
              {c.items.map((s) => (
                <li key={s.name} className="text-sm">
                  <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                    <span className="font-medium">{s.name}</span>
                    <span className="text-xs text-accent">{skillLevelLabels[s.level]}</span>
                  </div>
                  <p className="text-xs leading-relaxed text-muted">{s.evidence}</p>
                </li>
              ))}
            </ul>
          ) : (
            <ul className="mt-4 flex flex-wrap gap-1.5">
              {c.items.map((s) => (
                <li key={s.name}>
                  <Tag>{s.name}</Tag>
                </li>
              ))}
            </ul>
          )}
        </section>
      ))}
    </div>
  );
}
