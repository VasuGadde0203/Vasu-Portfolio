import { SkillsGrid } from "../components/SkillsGrid";
import { Container, SectionHeading } from "../components/ui";
import { skillCategories, skillLevelLabels } from "../data/skills";
import { usePageMeta } from "../lib/usePageMeta";

export default function Skills() {
  usePageMeta("Skills", "Technical skills of Vasu Gadde grouped by area, each with the documented evidence it is based on.");
  return (
    <Container className="py-16">
      <SectionHeading
        as="h1"
        eyebrow="Skills"
        title="Skills and the evidence behind them"
        intro="No ratings or percentages. Each skill carries an evidence-based label and a note on where it appears in my documented experience."
      />
      <dl className="mb-10 grid gap-3 text-xs text-muted sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(skillLevelLabels).map(([key, label]) => (
          <div key={key} className="rounded-xl border border-line bg-surface p-4">
            <dt className="font-medium text-ink">{label}</dt>
            <dd className="mt-1">
              {key === "professional" && "Used in my employment, per the resume."}
              {key === "projects" && "Used in documented projects."}
              {key === "familiar" && "Listed on the resume, with limited or unspecified documented usage."}
              {key === "exploring" && "Not currently assigned to any skill."}
            </dd>
          </div>
        ))}
      </dl>
      <SkillsGrid categories={skillCategories} showEvidence />
    </Container>
  );
}
