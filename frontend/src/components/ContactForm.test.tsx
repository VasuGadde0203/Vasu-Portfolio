import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ContactForm } from "./ContactForm";

afterEach(() => vi.unstubAllGlobals());

const fill = () => {
  fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Asha Rao" } });
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "asha@example.com" } });
  fireEvent.change(screen.getByLabelText("Message"), { target: { value: "Hello Vasu, let's talk about a role." } });
};

describe("ContactForm", () => {
  it("validates before sending", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<ContactForm />);
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    expect(screen.getByText("Enter your name.")).toBeInTheDocument();
    expect(screen.getByText("Enter a valid email address.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("posts the message with an empty honeypot and shows a confirmation", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "received" }) });
    vi.stubGlobal("fetch", fetchMock);
    render(<ContactForm />);
    fill();
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    expect(await screen.findByText("Message sent")).toBeInTheDocument();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/contact$/);
    expect(JSON.parse(init.body)).toEqual({
      name: "Asha Rao",
      email: "asha@example.com",
      message: "Hello Vasu, let's talk about a role.",
      website: "",
    });
  });

  it("shows the server's message when sending fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 429, json: async () => ({ error: { message: "Too many messages sent." } }) }),
    );
    render(<ContactForm />);
    fill();
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Too many messages sent.");
  });
});
