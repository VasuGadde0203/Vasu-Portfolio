import { Container, ButtonLink } from "../components/ui";
import { usePageMeta } from "../lib/usePageMeta";

export default function NotFound() {
  usePageMeta("Page not found", "The page you are looking for does not exist.");
  return (
    <Container className="py-28">
      <p className="text-sm text-accent">404</p>
      <h1 className="mt-3 font-display text-4xl font-semibold tracking-tight">That page doesn't exist</h1>
      <p className="mt-4 max-w-lg text-muted">The link may be outdated or mistyped.</p>
      <div className="mt-8 flex gap-3">
        <ButtonLink to="/" variant="primary">Go home</ButtonLink>
        <ButtonLink to="/projects">Browse projects</ButtonLink>
      </div>
    </Container>
  );
}
