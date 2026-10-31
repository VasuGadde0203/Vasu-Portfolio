import { describe, expect, it } from "vitest";
import { filterCategories, profile } from "./profile";
import { projects } from "./projects";
import { skillCategories } from "./skills";

describe("generated data", () => {
  it("has the documented projects with unique ids and no removed ones", () => {
    expect(projects).toHaveLength(14);
    expect(new Set(projects.map((p) => p.id)).size).toBe(14);
    const ids = projects.map((p) => p.id);
    expect(ids).not.toContain("timesnap");
    expect(ids).not.toContain("compliance-browser-automation");
    expect(ids).toContain("expense-sheet-extraction");
  });

  it("links personal GitHub projects to the owner's GitHub account only", () => {
    const personal = projects.filter((p) => p.links.length > 0);
    expect(personal.length).toBeGreaterThanOrEqual(6);
    for (const p of personal) for (const l of p.links) expect(l.url).toMatch(/^https:\/\/github\.com\/VasuGadde0203\//);
  });

  it("only references existing projects", () => {
    const ids = new Set(projects.map((p) => p.id));
    for (const p of projects) p.related_projects.forEach((r) => expect(ids.has(r)).toBe(true));
    for (const e of profile.experience) {
      e.related_projects.forEach((r) => expect(ids.has(r)).toBe(true));
      e.responsibilities.forEach((r) => r.projects.forEach((x) => expect(ids.has(x)).toBe(true)));
    }
  });

  it("uses only known filter categories", () => {
    for (const p of projects) p.filters.forEach((f) => expect(filterCategories).toContain(f));
    for (const c of filterCategories) expect(projects.some((p) => p.filters.includes(c))).toBe(true);
  });

  it("keeps the phone number private by default", () => {
    expect(profile.contact.phone).toBeNull();
    expect(JSON.stringify(profile)).not.toMatch(/(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)/);
  });

  it("preserves the documented chronology and 8 + 5 responsibilities", () => {
    const [jhs, supermoney] = profile.experience;
    expect(jhs.employer).toBe("JHS & Associates LLP");
    expect(jhs.responsibilities).toHaveLength(8);
    expect(supermoney.employer).toBe("Supermoney Advisors Private Limited");
    expect(supermoney.responsibilities).toHaveLength(5);
  });

  it("uses only evidence-based skill labels", () => {
    const levels = new Set(skillCategories.flatMap((c) => c.items.map((s) => s.level)));
    for (const l of levels) expect(["professional", "projects", "familiar", "exploring"]).toContain(l);
  });
});
