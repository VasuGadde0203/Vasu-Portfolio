import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

interface ChatUi {
  open: boolean;
  openChat: (prefill?: string) => void;
  closeChat: () => void;
  prefill: string | null;
  clearPrefill: () => void;
}

const Ctx = createContext<ChatUi | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [prefill, setPrefill] = useState<string | null>(null);
  const value = useMemo<ChatUi>(
    () => ({
      open,
      prefill,
      openChat: (text) => {
        setPrefill(text ?? null);
        setOpen(true);
      },
      closeChat: () => setOpen(false),
      clearPrefill: () => setPrefill(null),
    }),
    [open, prefill],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useChatUi(): ChatUi {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useChatUi must be used inside ChatProvider");
  return ctx;
}
