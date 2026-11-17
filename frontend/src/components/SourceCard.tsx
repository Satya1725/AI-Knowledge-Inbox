import { useState } from "react";
import { ExternalLink, Link2, StickyNote } from "lucide-react";
import type { Source } from "../api/types";
import { hostname } from "../utils/format";

interface SourceCardProps {
  source: Source;
  highlighted: boolean;
}

// Roughly 3 lines at this width; shorter snippets don't need a "Show more" toggle.
const LONG_SNIPPET_CHARS = 240;

export function SourceCard({ source, highlighted }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false);
  const isUrl = source.source_type === "url";
  const Icon = isUrl ? Link2 : StickyNote;
  const relevance = Math.round(Math.max(0, Math.min(1, source.score)) * 100);
  const isLong = source.snippet.length > LONG_SNIPPET_CHARS;

  return (
    <li
      id={`source-${source.index}`}
      className={`scroll-mt-6 rounded-xl border p-4 transition duration-500 ${
        highlighted
          ? "border-emerald-400 bg-emerald-50/60 ring-4 ring-emerald-100"
          : source.cited
            ? "border-slate-200 bg-white"
            : "border-dashed border-slate-200 bg-slate-50/50"
      }`}
    >
      <div className="flex items-start gap-3">
        <span
          className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-xs font-semibold ${
            source.cited ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-600"
          }`}
        >
          {source.index}
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <Icon className={`h-3.5 w-3.5 ${isUrl ? "text-sky-500" : "text-amber-500"}`} />
            <span className="truncate text-sm font-medium text-slate-900">{source.title || "Untitled"}</span>
            {isUrl && source.url && (
              <a
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-0.5 text-xs text-sky-600 hover:underline"
              >
                {hostname(source.url)}
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
            {!source.cited && <span className="text-[11px] text-slate-400">not cited</span>}
          </div>

          <blockquote
            className={`mt-2 border-l-2 border-slate-200 pl-3 text-[13px] leading-relaxed text-slate-600 ${
              expanded ? "" : "line-clamp-3"
            }`}
          >
            {source.snippet}
          </blockquote>
          {isLong && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="mt-1 text-xs font-medium text-emerald-600 hover:text-emerald-800"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}

          <div className="mt-3 flex items-center gap-2" title={`Cosine similarity ${source.score.toFixed(3)}`}>
            <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-linear-to-r from-emerald-400 to-teal-500" style={{ width: `${relevance}%` }} />
            </div>
            <span className="text-[11px] tabular-nums text-slate-400">{relevance}% match</span>
          </div>
        </div>
      </div>
    </li>
  );
}
