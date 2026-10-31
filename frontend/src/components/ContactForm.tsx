import { useState, type FormEvent } from "react";
import { CONTACT_LIMITS, ChatApiError, sendContact } from "../lib/api";
import { buttonClasses } from "./ui";

type Status = "idle" | "sending" | "sent" | "error";
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/;

const field =
  "w-full rounded-lg border border-line bg-bg px-3.5 py-2.5 text-sm text-ink placeholder:text-muted/70 hover:border-accent/60 focus:border-accent";

export function ContactForm() {
  const [values, setValues] = useState({ name: "", email: "", message: "", website: "" });
  const [errors, setErrors] = useState<Partial<Record<"name" | "email" | "message", string>>>({});
  const [status, setStatus] = useState<Status>("idle");
  const [serverError, setServerError] = useState("");

  const set = (k: keyof typeof values) => (e: { target: { value: string } }) =>
    setValues((v) => ({ ...v, [k]: e.target.value }));

  const validate = () => {
    const next: typeof errors = {};
    if (!values.name.trim()) next.name = "Enter your name.";
    if (!EMAIL.test(values.email.trim())) next.email = "Enter a valid email address.";
    if (values.message.trim().length < CONTACT_LIMITS.minMessage)
      next.message = `Write at least ${CONTACT_LIMITS.minMessage} characters.`;
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (status === "sending" || !validate()) return;
    setStatus("sending");
    setServerError("");
    try {
      await sendContact({ ...values, name: values.name.trim(), email: values.email.trim(), message: values.message.trim() });
      setStatus("sent");
      setValues({ name: "", email: "", message: "", website: "" });
    } catch (err) {
      setServerError(err instanceof ChatApiError ? err.message : "Something went wrong. Please try again.");
      setStatus("error");
    }
  };

  if (status === "sent") {
    return (
      <div role="status" className="rounded-2xl border border-line bg-surface p-8">
        <h2 className="font-display text-2xl font-semibold">Message sent</h2>
        <p className="mt-2 text-sm text-muted">Thanks for reaching out. I'll get back to you by email.</p>
        <button type="button" className={`${buttonClasses.secondary} mt-6`} onClick={() => setStatus("idle")}>
          Send another message
        </button>
      </div>
    );
  }

  const err = (id: string, text?: string) =>
    text ? (
      <p id={id} className="mt-1.5 text-xs text-red-300">
        {text}
      </p>
    ) : null;

  return (
    <form onSubmit={submit} noValidate className="rounded-2xl border border-line bg-surface p-6 sm:p-8">
      <h2 className="font-display text-2xl font-semibold">Send a message</h2>
      <div className="mt-6 grid gap-5">
        <div>
          <label htmlFor="c-name" className="mb-1.5 block text-sm font-medium">Name</label>
          <input id="c-name" className={field} value={values.name} onChange={set("name")} maxLength={CONTACT_LIMITS.maxName}
            autoComplete="name" aria-invalid={!!errors.name} aria-describedby={errors.name ? "c-name-err" : undefined} />
          {err("c-name-err", errors.name)}
        </div>
        <div>
          <label htmlFor="c-email" className="mb-1.5 block text-sm font-medium">Email</label>
          <input id="c-email" type="email" className={field} value={values.email} onChange={set("email")} autoComplete="email"
            placeholder="name@company.com" aria-invalid={!!errors.email} aria-describedby={errors.email ? "c-email-err" : undefined} />
          {err("c-email-err", errors.email)}
        </div>
        <div>
          <label htmlFor="c-message" className="mb-1.5 block text-sm font-medium">Message</label>
          <textarea id="c-message" rows={6} className={`${field} resize-y`} value={values.message} onChange={set("message")}
            maxLength={CONTACT_LIMITS.maxMessage} aria-invalid={!!errors.message}
            aria-describedby={errors.message ? "c-message-err" : undefined} />
          <div className="flex justify-between">
            {err("c-message-err", errors.message) ?? <span />}
            <p className="mt-1.5 text-xs text-muted">{values.message.length}/{CONTACT_LIMITS.maxMessage}</p>
          </div>
        </div>
        {/* Honeypot: hidden from people and assistive tech; bots tend to fill it in. */}
        <div aria-hidden="true" className="absolute -left-[9999px] h-0 w-0 overflow-hidden">
          <label>Website<input tabIndex={-1} autoComplete="off" value={values.website} onChange={set("website")} /></label>
        </div>
      </div>
      {status === "error" && <p role="alert" className="mt-5 text-sm text-red-300">{serverError}</p>}
      <button type="submit" disabled={status === "sending"} className={`${buttonClasses.primary} mt-6 disabled:opacity-60`}>
        {status === "sending" ? "Sending…" : "Send message"}
      </button>
    </form>
  );
}
