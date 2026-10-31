import ReactMarkdown from "react-markdown";
import { Link } from "react-router-dom";
import { getProject } from "../../data/projects";

const SAFE_ABSOLUTE = /^(https?:|mailto:)/i;

// Site pages the assistant may mention by path. A bare path such as /projects/invoice-extraction
// (not already inside a Markdown link) is turned into a link so visitors can click it.
const PAGE_LABELS: Record<string, string> = {
  "/projects": "Projects",
  "/skills": "Skills",
  "/experience": "Experience",
  "/about": "About",
  "/contact": "Contact",
  "/resume": "Resume",
};
const BARE_PATH = /(?<![\w\])(/:.#-])(\/projects\/[a-z0-9-]*[a-z0-9]|\/(?:projects|skills|experience|about|contact|resume)(?![\w/-]))/g;

export function linkifyPaths(text: string): string {
  return text.replace(BARE_PATH, (path) => {
    if (path.startsWith("/projects/")) {
      const project = getProject(path.slice("/projects/".length));
      return project ? `[${project.title}](${path})` : path; // never link a page that does not exist
    }
    return `[${PAGE_LABELS[path]}](${path})`;
  });
}

/** Renders model output as Markdown. Raw HTML is never rendered (react-markdown escapes it),
 *  and link targets are restricted to http(s), mailto and in-site paths. */
export function SafeMarkdown({ text, onNavigate }: { text: string; onNavigate?: () => void }) {
  return (
    <div className="prose-chat">
      <ReactMarkdown
        skipHtml
        components={{
          a({ href, children }) {
            if (href && href.startsWith("/") && !href.startsWith("//")) {
              return <Link to={href} onClick={onNavigate}>{children}</Link>;
            }
            if (href && SAFE_ABSOLUTE.test(href)) {
              return (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              );
            }
            return <span>{children}</span>;
          },
          img: () => null,
        }}
      >
        {linkifyPaths(text)}
      </ReactMarkdown>
    </div>
  );
}
