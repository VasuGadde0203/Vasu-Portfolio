import { Hero } from "../components/home/Hero";
import { AboutSection, ContactBlock, ExperienceSection, ProjectsSection, ServicesSection, SkillsSection } from "../components/home/Sections";
import { profile } from "../data/profile";
import { usePageMeta } from "../lib/usePageMeta";

export default function Home() {
  usePageMeta(null, profile.tagline);
  return (
    <>
      <Hero />
      <AboutSection />
      <ServicesSection />
      <SkillsSection />
      <ProjectsSection />
      <ExperienceSection />
      <ContactBlock />
    </>
  );
}
