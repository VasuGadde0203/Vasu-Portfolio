import { useChatUi } from "../components/chat/ChatContext";
import { ContactDetails } from "../components/ContactSection";
import { ContactForm } from "../components/ContactForm";
import { Container, SectionHeading, buttonClasses } from "../components/ui";
import { usePageMeta } from "../lib/usePageMeta";

export default function Contact() {
  const { openChat } = useChatUi();
  usePageMeta("Contact", "Send a message to Vasu Gadde, or reach him by email, LinkedIn or GitHub.");
  return (
    <Container className="py-16">
      <SectionHeading
        as="h1"
        eyebrow="Contact"
        title="Get in touch"
        intro="Send a message below and I'll reply by email. You can also ask the assistant about my documented background first."
      />
      <div className="grid gap-10 lg:grid-cols-[1.2fr_1fr]">
        <ContactForm />
        <div>
          <h2 className="mb-4 font-display text-xl font-semibold">Other ways to reach me</h2>
          <ContactDetails />
          <button type="button" className={`${buttonClasses.secondary} mt-6`} onClick={() => openChat("How can I contact him?")}>
            Ask Vasu AI
          </button>
        </div>
      </div>
    </Container>
  );
}
