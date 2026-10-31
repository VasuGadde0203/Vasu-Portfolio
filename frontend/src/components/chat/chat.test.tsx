import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ChatProvider, useChatUi } from "./ChatContext";
import { ChatWidget } from "./ChatWidget";
import { SafeMarkdown } from "./SafeMarkdown";

function Harness() {
  const { openChat } = useChatUi();
  return (
    <>
      <button onClick={() => openChat()}>open</button>
      <ChatWidget />
    </>
  );
}

const renderChat = () =>
  render(
    <MemoryRouter>
      <ChatProvider>
        <Harness />
      </ChatProvider>
    </MemoryRouter>,
  );

afterEach(() => vi.unstubAllGlobals());

describe("SafeMarkdown", () => {
  it("does not render raw HTML or unsafe links", () => {
    const { container } = render(
      <MemoryRouter>
        <SafeMarkdown text={'Intro <script>alert(1)</script> and <img src=x onerror=alert(1)> text\n\n[bad](javascript:alert(1)) and [ok](https://example.com)'} />
      </MemoryRouter>,
    );
    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector('a[href^="javascript"]')).toBeNull();
    expect(container.querySelector('a[href="https://example.com"]')).not.toBeNull();
  });
});

describe("page links in answers", () => {
  const html = (text: string) =>
    render(
      <MemoryRouter>
        <SafeMarkdown text={text} />
      </MemoryRouter>,
    ).container;

  it("turns a bare project path into a clickable in-site link", () => {
    const c = html("For details, you can check the project page at /projects/invoice-extraction.");
    const a = c.querySelector('a[href="/projects/invoice-extraction"]');
    expect(a).not.toBeNull();
    expect(a?.textContent).not.toContain("/projects"); // readable label, not the raw path
  });

  it("does not double-link a path that is already a Markdown link", () => {
    const c = html("See [the case study](/projects/invoice-extraction) for more.");
    expect(c.querySelectorAll("a")).toHaveLength(1);
    expect(c.querySelector("a")?.textContent).toBe("the case study");
  });

  it("does not link a project page that does not exist", () => {
    expect(html("See /projects/not-a-real-project for more.").querySelector("a")).toBeNull();
  });

  it("links other site pages but leaves look-alike text alone", () => {
    const c = html("Try /skills or /contact. Not a link: example.com/projects/x and /projectsfoo.");
    expect([...c.querySelectorAll("a")].map((a) => a.getAttribute("href"))).toEqual(["/skills", "/contact"]);
  });
});

describe("ChatWidget", () => {
  it("shows the disclosure and suggested questions, and sends a question to the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        answer: "Documented answer.",
        sources: [{ document_id: "project-invoice-extraction", title: "AI Invoice & PDF Extraction", section: "Overview", project_id: "invoice-extraction", url: "/projects/invoice-extraction" }],
        project_ids: ["invoice-extraction"],
        evidence: "strong",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    renderChat();
    fireEvent.click(screen.getByRole("button", { name: "Open Ask Vasu AI chat" }));
    expect(screen.getByText(/AI assistant representing Vasu Gadde/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "What is his experience with RAG?" }));
    expect(await screen.findByText("Documented answer.")).toBeInTheDocument();
    expect(screen.queryByText("Sources")).toBeNull(); // sources are returned by the API but not displayed
    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse(init.body)).toEqual({ message: "What is his experience with RAG?", history: [] });

    fireEvent.change(screen.getByLabelText("Your question"), { target: { value: "What did he use?" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(JSON.parse(fetchMock.mock.calls[1][1].body).history).toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(screen.queryByText("Documented answer.")).toBeNull();
  });

  it("shows an error with a retry action and keeps Send disabled for empty input", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({ error: { message: "The assistant is temporarily unavailable." } }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ answer: "Back.", sources: [], project_ids: [], evidence: "partial" }) });
    vi.stubGlobal("fetch", fetchMock);
    renderChat();
    fireEvent.click(screen.getByRole("button", { name: "Open Ask Vasu AI chat" }));
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Your question"), { target: { value: "Hello" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("temporarily unavailable");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("Back.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
