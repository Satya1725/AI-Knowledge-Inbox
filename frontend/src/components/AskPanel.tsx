import { useEffect, useState, type FormEvent } from "react";
import { ArrowUp, Loader2, MessageSquareText } from "lucide-react";
import type { ProviderName, ProvidersInfo } from "../api/types";
import { useAsk } from "../hooks/useAsk";
import { PROVIDER_LABELS } from "../utils/format";
import { AnswerView } from "./AnswerView";
import { Card } from "./ui/Card";
import { ErrorBanner } from "./ui/ErrorBanner";
import { LoadingDots } from "./ui/LoadingDots";

const EXAMPLE_QUESTIONS = [
  "Summarize everything I've saved",
  "What are the key takeaways from my links?",
  "What did I note about deadlines?",
];

interface AskPanelProps {
  providers: ProvidersInfo | null;
  readyItemCount: number;
}

export function AskPanel({ providers, readyItemCount }: AskPanelProps) {
  const [draft, setDraft] = useState("");
  const [provider, setProvider] = useState<ProviderName | undefined>(undefined);
  const { question, result, loading, error, ask } = useAsk();

  useEffect(() => {
    if (providers && !provider) setProvider(providers.default_chat_provider);
  }, [providers, provider]);

  const canAsk = draft.trim().length >= 3 && !loading;

  function submit(text: string) {
    const trimmed = text.trim();
    if (trimmed.length < 3 || loading) return;
    setDraft(trimmed);
    ask(trimmed, provider);
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    submit(draft);
  }

  const providerSwitch =
    providers && providers.available_chat_providers.length > 1 ? (
      <div className="flex rounded-lg bg-slate-100 p-0.5 text-xs">
        {providers.available_chat_providers.map((name) => (
          <button
            key={name}
            type="button"
            onClick={() => setProvider(name)}
            className={`rounded-md px-2.5 py-1 font-medium transition ${
              provider === name ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
            }`}
          >
            {PROVIDER_LABELS[name]}
          </button>
        ))}
      </div>
    ) : null;

  return (
    <Card
      title="Ask your inbox"
      subtitle="Answers come only from what you've saved"
      icon={<MessageSquareText className="h-4 w-4" />}
      action={providerSwitch}
      className="lg:sticky lg:top-6 lg:self-start"
    >
      <form onSubmit={handleSubmit} className="relative">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit(draft);
            }
          }}
          placeholder="Ask a question about your notes and links…"
          rows={2}
          maxLength={1000}
          className="w-full resize-none rounded-xl border border-slate-200 bg-white py-3 pl-4 pr-14 text-[15px] text-slate-800 shadow-sm placeholder:text-slate-400 focus:border-violet-400 focus:outline-none focus:ring-4 focus:ring-violet-100"
        />
        <button
          type="submit"
          disabled={!canAsk}
          className="absolute bottom-3.5 right-3 flex h-9 w-9 items-center justify-center rounded-lg bg-linear-to-br from-violet-500 to-indigo-600 text-white shadow-md shadow-violet-500/30 transition hover:brightness-110 disabled:cursor-not-allowed disabled:from-slate-300 disabled:to-slate-300 disabled:shadow-none"
          aria-label="Ask"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
        </button>
      </form>
      <p className="mt-1.5 text-[11px] text-slate-400">Enter to ask · Shift+Enter for a new line</p>

      <div className="mt-6">
        {error && <ErrorBanner message={error} />}

        {loading && <AnswerSkeleton providerLabel={provider ? PROVIDER_LABELS[provider] : "AI"} />}

        {!loading && result && question && <AnswerView question={question} result={result} />}

        {!loading && !result && !error && (
          <EmptyState readyItemCount={readyItemCount} onPick={(q) => submit(q)} />
        )}
      </div>
    </Card>
  );
}

const STEP_INTERVAL_MS = 1400;

/** Shown while /query is in flight. The step text is a hint of what the server is doing, not real progress. */
function AnswerSkeleton({ providerLabel }: { providerLabel: string }) {
  const steps = ["Understanding your question", "Searching your saved content", `Writing an answer with ${providerLabel}`];
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setStep((s) => Math.min(s + 1, steps.length - 1)), STEP_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [steps.length]);

  return (
    <div className="animate-fade-in rounded-xl border border-violet-100 bg-linear-to-b from-violet-50/60 to-white p-5">
      <div className="flex items-center gap-3">
        <LoadingDots />
        <span key={step} className="animate-fade-in text-sm font-medium text-violet-700">
          {steps[step]}…
        </span>
      </div>

      <ol className="mt-4 flex gap-1.5">
        {steps.map((label, i) => (
          <li
            key={label}
            className={`h-1 flex-1 rounded-full transition-colors duration-500 ${i <= step ? "bg-violet-500" : "bg-violet-100"}`}
          />
        ))}
      </ol>

      <div className="mt-5 animate-pulse space-y-2.5">
        <div className="h-3 w-full rounded bg-slate-100" />
        <div className="h-3 w-11/12 rounded bg-slate-100" />
        <div className="h-3 w-3/5 rounded bg-slate-100" />
      </div>
    </div>
  );
}

function EmptyState({ readyItemCount, onPick }: { readyItemCount: number; onPick: (q: string) => void }) {
  if (readyItemCount === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 px-6 py-12 text-center">
        <p className="text-sm font-medium text-slate-700">Your inbox is empty</p>
        <p className="mt-1 text-sm text-slate-400">Save a note or a URL first, then ask questions about it here.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-dashed border-slate-200 px-6 py-10 text-center">
      <p className="text-sm text-slate-500">
        Searching across <span className="font-medium text-slate-700">{readyItemCount}</span> indexed item
        {readyItemCount === 1 ? "" : "s"}. Try one of these:
      </p>
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {EXAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => onPick(q)}
            className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 transition hover:border-violet-300 hover:text-violet-700"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
