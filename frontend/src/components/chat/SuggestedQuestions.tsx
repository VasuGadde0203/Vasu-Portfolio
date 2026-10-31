export const SUGGESTED_QUESTIONS = [
  "Tell me about Vasu.",
  "Explain his AI invoice processing project.",
  "What is his experience with RAG?",
  "Tell me about his recruitment automation platform.",
  "What technologies has he used?",
  "What did he build at JHS & Associates LLP?",
];

export function SuggestedQuestions({ onPick, disabled }: { onPick: (q: string) => void; disabled?: boolean }) {
  return (
    <div>
      <p className="mb-2 text-xs text-muted">Try asking:</p>
      <ul className="flex flex-wrap gap-2">
        {SUGGESTED_QUESTIONS.map((q) => (
          <li key={q}>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onPick(q)}
              className="rounded-full border border-line bg-surface px-3 py-1.5 text-left text-xs text-ink transition-colors hover:border-accent hover:bg-surface-2 hover:text-accent disabled:opacity-50"
            >
              {q}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
