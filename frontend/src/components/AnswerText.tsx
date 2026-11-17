import type { ReactNode } from "react";

/**
 * Renders the LLM answer: paragraphs, bullet lists, **bold**, and [n] citations
 * as clickable chips. Deliberately tiny -- not a full markdown parser.
 */

interface AnswerTextProps {
  text: string;
  onCitationClick: (index: number) => void;
}

const INLINE_TOKEN = /(\*\*[^*]+\*\*|\[\d+\])/g;
const LIST_LINE = /^\s*(?:[-*•]|\d+\.)\s+/;

export function AnswerText({ text, onCitationClick }: AnswerTextProps) {
  const blocks = text.split(/\n{2,}/).filter((b) => b.trim());

  function renderInline(line: string): ReactNode[] {
    return line.split(INLINE_TOKEN).map((part, i) => {
      const citation = part.match(/^\[(\d+)\]$/);
      if (citation) {
        const index = Number(citation[1]);
        return (
          <button
            key={i}
            onClick={() => onCitationClick(index)}
            className="mx-0.5 inline-flex h-[18px] min-w-[18px] -translate-y-px items-center justify-center rounded-md bg-emerald-100 px-1 align-middle text-[11px] font-semibold text-emerald-700 transition hover:bg-emerald-600 hover:text-white"
            title={`Jump to source ${index}`}
          >
            {index}
          </button>
        );
      }
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={i} className="font-semibold text-slate-900">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return part;
    });
  }

  return (
    <div className="space-y-3 text-[15px] leading-7 text-slate-700">
      {blocks.map((block, i) => {
        const lines = block.split("\n").filter((l) => l.trim());
        if (lines.every((l) => LIST_LINE.test(l))) {
          return (
            <ul key={i} className="list-disc space-y-1 pl-5 marker:text-emerald-400">
              {lines.map((line, j) => (
                <li key={j}>{renderInline(line.replace(LIST_LINE, ""))}</li>
              ))}
            </ul>
          );
        }
        return (
          <p key={i} className="whitespace-pre-line">
            {renderInline(block)}
          </p>
        );
      })}
    </div>
  );
}
