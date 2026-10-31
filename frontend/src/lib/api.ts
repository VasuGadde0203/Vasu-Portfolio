import type { ChatResponse } from "../types";

export const API_BASE_URL: string = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export const CHAT_LIMITS = { maxMessageChars: 600, maxHistoryMessages: 6, maxHistoryChars: 1500 } as const;

export interface HistoryTurn {
  role: "user" | "assistant";
  content: string;
}

export class ChatApiError extends Error {
  constructor(
    message: string,
    readonly status: number | null,
    readonly retryable: boolean,
  ) {
    super(message);
  }
}

const GENERIC = "The assistant is unavailable right now. Please try again, or email me directly.";

export interface ContactPayload {
  name: string;
  email: string;
  message: string;
  website: string; // honeypot, always empty for real visitors
}

export const CONTACT_LIMITS = { maxName: 100, minMessage: 10, maxMessage: 2000 } as const;

export async function sendContact(payload: ContactPayload): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/contact`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ChatApiError("Couldn't reach the server. Please try again, or email me directly.", null, true);
  }
  if (res.ok) return;
  let detail = "Your message couldn't be sent right now. Please email me directly.";
  try {
    const body = await res.json();
    if (res.status === 422) detail = "Please check your name, email and message and try again.";
    else if (typeof body?.error?.message === "string") detail = body.error.message;
  } catch {
    /* keep generic message */
  }
  throw new ChatApiError(detail, res.status, res.status !== 422);
}

export async function sendChat(
  message: string,
  history: HistoryTurn[],
  signal?: AbortSignal,
): Promise<ChatResponse> {
  const timeout = new AbortController();
  const timer = setTimeout(() => timeout.abort(), 45_000);
  signal?.addEventListener("abort", () => timeout.abort());
  try {
    const res = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        history: history.slice(-CHAT_LIMITS.maxHistoryMessages).map((t) => ({
          role: t.role,
          content: t.content.slice(0, CHAT_LIMITS.maxHistoryChars),
        })),
      }),
      signal: timeout.signal,
    });
    if (res.ok) return (await res.json()) as ChatResponse;
    let detail = GENERIC;
    try {
      const body = await res.json();
      if (res.status === 422) detail = "That message couldn't be sent. Try a shorter question.";
      else if (typeof body?.error?.message === "string") detail = body.error.message;
    } catch {
      /* keep generic message */
    }
    throw new ChatApiError(detail, res.status, res.status !== 413 && res.status !== 422);
  } catch (err) {
    if (err instanceof ChatApiError) throw err;
    if (signal?.aborted) throw err;
    throw new ChatApiError(
      timeout.signal.aborted ? "The assistant took too long to respond." : GENERIC,
      null,
      true,
    );
  } finally {
    clearTimeout(timer);
  }
}
