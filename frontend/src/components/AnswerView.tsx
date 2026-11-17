import { useEffect, useState } from "react";
import { Quote, Sparkles } from "lucide-react";
import type { QueryResponse } from "../api/types";
import { PROVIDER_LABELS } from "../utils/format";
import { AnswerText } from "./AnswerText";
import { SourceCard } from "./SourceCard";

interface AnswerViewProps {
  question: string;
  result: QueryResponse;
}

export function AnswerView({ question, result }: AnswerViewProps) {
  const [highlighted, setHighlighted] = useState<number | null>(null);

  // Clear the highlight a moment after jumping to a source.
  useEffect(() => {
    if (highlighted === null) return;
    const timer = setTimeout(() => setHighlighted(null), 1800);
    return () => clearTimeout(timer);
  }, [highlighted]);

  function jumpToSource(index: number) {
    document.getElementById(`source-${index}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    setHighlighted(index);
  }

  const citedCount = result.sources.filter((s) => s.cited).length;

  return (
    <div className="animate-fade-in space-y-6">
      <div className="rounded-xl border border-violet-100 bg-linear-to-b from-violet-50/70 to-white p-5">
        <div className="mb-3 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-violet-600">
            <Sparkles className="h-3.5 w-3.5" />
            Answer
          </div>
          {result.provider && (
            <span className="rounded-full bg-white px-2 py-0.5 text-[11px] text-slate-500 ring-1 ring-slate-200">
              via {PROVIDER_LABELS[result.provider]}
            </span>
          )}
        </div>
        <p className="mb-3 text-sm font-medium text-slate-500">“{question}”</p>
        <AnswerText text={result.answer} onCitationClick={jumpToSource} />
      </div>

      {result.sources.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Quote className="h-4 w-4 text-slate-400" />
            Sources
            <span className="font-normal text-slate-400">
              {citedCount} cited of {result.sources.length} retrieved
            </span>
          </h3>
          <ul className="space-y-2.5">
            {result.sources.map((source) => (
              <SourceCard key={source.index} source={source} highlighted={highlighted === source.index} />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
