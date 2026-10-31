import { useState } from "react";
import { SafeMarkdown } from "./SafeMarkdown";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  error?: boolean;
}

interface Props {
  message: Message;
  onRetry?: () => void;
  onNavigate?: () => void;
}

export function ChatMessage({ message, onRetry, onNavigate }: Props) {
  const [copied, setCopied] = useState(false);

  if (message.role === "user") {
    return (
      <li className="flex justify-end">
        <p className="max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-sm bg-accent-strong px-3.5 py-2 text-sm text-on-accent">
          {message.content}
        </p>
      </li>
    );
  }

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <li className="flex">
      <div
        className={`max-w-[92%] rounded-2xl rounded-bl-sm border px-3.5 py-2.5 text-sm leading-relaxed ${
          message.error ? "border-red-400/40 bg-red-950/40 text-red-100" : "border-line bg-surface-2"
        }`}
      >
        {message.error ? <p role="alert">{message.content}</p> : <SafeMarkdown text={message.content} onNavigate={onNavigate} />}
        {message.error ? (
          onRetry && (
            <button type="button" onClick={onRetry} className="mt-2 rounded px-1 text-xs font-medium text-accent underline underline-offset-2 hover:bg-surface-2">
              Retry
            </button>
          )
        ) : (
          <>
            <button type="button" onClick={copy} className="mt-2 rounded px-1 text-xs text-muted hover:bg-surface hover:text-ink">
              {copied ? "Copied" : "Copy response"}
            </button>
          </>
        )}
      </div>
    </li>
  );
}
