import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { ExperienceTimeline } from "../components/ExperienceTimeline";
import { Container, SectionHeading } from "../components/ui";
import { profile } from "../data/profile";
import { usePageMeta } from "../lib/usePageMeta";

export default function Experience() {
  usePageMeta("Experience", "Professional experience: Data Scientist & AI Engineer at JHS & Associates LLP and Machine Learning Intern at Supermoney Advisors.");
  const { hash } = useLocation();
  useEffect(() => {
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView();
  }, [hash]);
  return (
    <Container className="py-16">
      <SectionHeading
        as="h1"
        eyebrow="Experience"
        title="Professional experience"
        intro="Responsibilities are listed as documented, using the original wording of the contribution (developed, automated, worked on, restructured, authored, built)."
      />
      <ExperienceTimeline entries={profile.experience} />
    </Container>
  );
}
