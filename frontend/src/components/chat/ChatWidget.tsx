import { useCallback, useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { CHAT_LIMITS, ChatApiError, sendChat, type HistoryTurn } from "../../lib/api";
import { ChatMessage, type Message } from "./ChatMessage";
import { useChatUi } from "./ChatContext";
import { SuggestedQuestions } from "./SuggestedQuestions";

const WELCOME =
  "Hi, I'm Ask Vasu AI. Ask me about Vasu's experience, projects, skills or how to get in touch.";
const DISCLOSURE =
  "AI assistant representing Vasu Gadde. Answers are generated from his professional portfolio and documented experience.";

let counter = 0;
const nextId = () => `m${++counter}`;

export function ChatWidget() {
  const { open, openChat, closeChat, prefill, clearPrefill } = useChatUi();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const launcherRef = useRef<HTMLButtonElement>(null);
  const wasOpen = useRef(false);

  // History is held only in memory: it is replayed to the backend as context and never persisted.
  const historyFrom = (list: Message[]): HistoryTurn[] =>
    list.filter((m) => !m.error).map((m) => ({ role: m.role, content: m.content }));

  const ask = useCallback(
    async (text: string, base: Message[]) => {
      const trimmed = text.trim();
      if (!trimmed || trimmed.length > CHAT_LIMITS.maxMessageChars) return;
      const userMsg: Message = { id: nextId(), role: "user", content: trimmed };
      const history = historyFrom(base);
      setMessages([...base, userMsg]);
      setInput("");
      setLoading(true);
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      try {
        const res = await sendChat(trimmed, history, controller.signal);
        setMessages((prev) => [
          ...prev,
          { id: nextId(), role: "assistant", content: res.answer },
        ]);
      } catch (err) {
        if (controller.signal.aborted) return;
        const message = err instanceof ChatApiError ? err.message : "Something went wrong. Please try again.";
        setMessages((prev) => [...prev, { id: nextId(), role: "assistant", content: message, error: true }]);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    },
    [],
  );

  const retry = () => {
    const lastUserIndex = messages.map((m) => m.role).lastIndexOf("user");
    if (lastUserIndex < 0 || loading) return;
    void ask(messages[lastUserIndex].content, messages.slice(0, lastUserIndex));
  };

  const clear = () => {
    abortRef.current?.abort();
    setMessages([]);
    setLoading(false);
    setInput("");
  };

  useEffect(() => {
    if (open) inputRef.current?.focus();
    else if (wasOpen.current) launcherRef.current?.focus();
    wasOpen.current = open;
  }, [open]);

  useEffect(() => {
    if (open && prefill) {
      void ask(prefill, messages);
      clearPrefill();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, prefill]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages, loading]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: globalThis.KeyboardEvent) => e.key === "Escape" && closeChat();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, closeChat]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!loading) void ask(input, messages);
  };
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      if (!loading) void ask(input, messages);
    }
  };

  // On phones the chat covers the whole screen, so follow a link by closing it; on larger screens it stays open.
  const closeOnSmallScreens = () => {
    if (window.matchMedia?.("(max-width: 639px)").matches) closeChat();
  };

  const tooLong = input.length > CHAT_LIMITS.maxMessageChars;
  const canSend = !loading && input.trim().length > 0 && !tooLong;

  return (
    <>
      {!open && (
        <button
          ref={launcherRef}
          type="button"
          onClick={() => openChat()}
          aria-label="Open Ask Vasu AI chat"
          className="fixed bottom-5 right-5 z-40 flex items-center gap-2 rounded-full bg-accent-strong px-4 py-3 text-sm font-medium text-on-accent shadow-lg shadow-black/50 transition-transform hover:scale-[1.05] hover:bg-[#f4a67f] hover:shadow-xl active:scale-100 focus-visible:outline-offset-4"
        >
          <span aria-hidden="true" className="inline-block h-2 w-2 rounded-full bg-emerald-300 ring-2 ring-black/20" />
          Ask Vasu AI
        </button>
      )}
      {open && (
        <section
          role="dialog"
          aria-label="Ask Vasu AI"
          className="fixed inset-0 z-50 flex flex-col border-line bg-surface sm:inset-auto sm:bottom-5 sm:right-5 sm:h-[640px] sm:max-h-[calc(100vh-2.5rem)] sm:w-[400px] sm:rounded-2xl sm:border sm:shadow-2xl sm:shadow-black/60"
        >
          <header className="flex items-start justify-between gap-3 border-b border-line px-4 py-3">
            <div>
              <h2 className="font-display text-base font-semibold">Ask Vasu AI</h2>
              <p className="flex items-center gap-1.5 text-xs text-muted">
                <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-sage" /> Online
              </p>
            </div>
            <div className="flex items-center gap-1">
              {messages.length > 0 && (
                <button type="button" onClick={clear} className="rounded-md px-2 py-1 text-xs text-muted hover:bg-surface-2 hover:text-ink">
                  Clear
                </button>
              )}
              <button
                type="button"
                onClick={closeChat}
                aria-label="Close chat"
                className="rounded-md px-2 py-1 text-lg leading-none text-muted hover:bg-surface-2 hover:text-ink"
              >
                ×
              </button>
            </div>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
            <p className="text-[11px] leading-snug text-muted">{DISCLOSURE}</p>
            <ul aria-live="polite" className="space-y-3">
              <li className="flex">
                <p className="max-w-[92%] rounded-2xl rounded-bl-sm border border-line bg-surface-2 px-3.5 py-2.5 text-sm">
                  {WELCOME}
                </p>
              </li>
              {messages.map((m, i) => (
                <ChatMessage
                  key={m.id}
                  message={m}
                  onRetry={m.error && i === messages.length - 1 ? retry : undefined}
                  onNavigate={closeOnSmallScreens}
                />
              ))}
              {loading && (
                <li className="flex" aria-label="Assistant is typing">
                  <span className="flex gap-1 rounded-2xl border border-line bg-surface-2 px-4 py-3">
                    <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted" />
                    <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted" />
                    <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted" />
                  </span>
                </li>
              )}
            </ul>
            {messages.length === 0 && <SuggestedQuestions disabled={loading} onPick={(q) => void ask(q, messages)} />}
            <div ref={endRef} />
          </div>

          <form onSubmit={submit} className="border-t border-line p-3">
            <div className="flex items-end gap-2">
              <label htmlFor="chat-input" className="sr-only">
                Your question
              </label>
              <textarea
                id="chat-input"
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                rows={1}
                placeholder="Ask about Vasu's experience…"
                aria-invalid={tooLong}
                className="max-h-28 min-h-[40px] flex-1 resize-none rounded-xl border border-line bg-bg px-3 py-2 text-sm placeholder:text-muted focus:border-accent"
              />
              <button
                type="submit"
                disabled={!canSend}
                className="h-10 rounded-xl bg-accent-strong px-4 text-sm font-medium text-on-accent hover:bg-[#f4a67f] disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-accent-strong"
              >
                Send
              </button>
            </div>
            <p className={`mt-1 text-right text-[11px] ${tooLong ? "text-red-300" : "text-muted"}`}>
              {input.length}/{CHAT_LIMITS.maxMessageChars} · Enter to send, Shift+Enter for a new line
            </p>
          </form>
        </section>
      )}
    </>
  );
}
