import { ExternalLink, Link2, RotateCw, StickyNote, Trash2 } from "lucide-react";
import type { Item } from "../api/types";
import { hostname, timeAgo } from "../utils/format";
import { StatusBadge } from "./StatusBadge";

export function itemDisplayTitle(item: Item): string {
  return item.title || (item.source_type === "url" ? hostname(item.url) : "Untitled note");
}

export function ItemTypeIcon({ item }: { item: Item }) {
  const isUrl = item.source_type === "url";
  const Icon = isUrl ? Link2 : StickyNote;
  return (
    <span
      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
        isUrl ? "bg-sky-50 text-sky-600" : "bg-amber-50 text-amber-600"
      }`}
    >
      <Icon className="h-4 w-4" />
    </span>
  );
}

interface ItemCardProps {
  item: Item;
  deleting: boolean;
  onRequestDelete: (item: Item) => void;
  onReindex: (item: Item) => void;
}

export function ItemCard({ item, deleting, onRequestDelete, onReindex }: ItemCardProps) {
  const isUrl = item.source_type === "url";
  const title = itemDisplayTitle(item);

  return (
    <li
      className={`group relative animate-fade-in overflow-hidden rounded-xl border bg-white p-3.5 transition hover:border-emerald-200 hover:shadow-sm ${
        item.status === "processing" ? "border-emerald-200" : "border-slate-200"
      } ${deleting ? "pointer-events-none opacity-50" : ""}`}
    >
      {item.status === "processing" && (
        <div className="absolute inset-x-0 bottom-0 h-0.5 overflow-hidden bg-emerald-100">
          <div className="h-full w-1/3 animate-indeterminate rounded-full bg-linear-to-r from-emerald-500 to-teal-500" />
        </div>
      )}

      <div className="flex gap-3">
        <ItemTypeIcon item={item} />

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="truncate text-sm font-medium text-slate-900" title={title}>
              {title}
            </h3>
            <div className="flex shrink-0 items-center gap-0.5 opacity-0 transition group-hover:opacity-100 focus-within:opacity-100">
              <button
                onClick={() => onReindex(item)}
                disabled={deleting || item.status === "processing"}
                className="rounded-md p-1 text-slate-400 transition hover:bg-emerald-50 hover:text-emerald-600 disabled:pointer-events-none disabled:opacity-40"
                aria-label="Re-index item"
                title={isUrl ? "Re-fetch and re-index this page" : "Re-index this note"}
              >
                <RotateCw className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => onRequestDelete(item)}
                disabled={deleting}
                className="rounded-md p-1 text-slate-400 transition hover:bg-red-50 hover:text-red-600"
                aria-label="Delete item"
                title="Delete"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {isUrl && item.url && (
            <a
              href={item.url}
              target="_blank"
              rel="noreferrer"
              className="mt-0.5 inline-flex items-center gap-1 text-xs text-sky-600 hover:underline"
            >
              {hostname(item.url)}
              <ExternalLink className="h-3 w-3" />
            </a>
          )}

          {item.preview && <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-slate-500">{item.preview}</p>}

          {item.status === "failed" && item.error && (
            <div className="mt-1.5 flex items-start justify-between gap-2 rounded-md bg-red-50 px-2 py-1 text-xs text-red-700">
              <span>{item.error}</span>
              <button onClick={() => onReindex(item)} className="shrink-0 font-medium underline hover:text-red-900">
                Retry
              </button>
            </div>
          )}

          <div className="mt-2 flex items-center gap-2 text-[11px] text-slate-400">
            <StatusBadge status={item.status} />
            <span>{timeAgo(item.created_at)}</span>
            {item.status === "processing" && (
              <span className="text-emerald-500">{isUrl ? "Fetching page & embedding…" : "Embedding…"}</span>
            )}
            {item.status === "ready" && (
              <>
                <span>·</span>
                <span>
                  {item.chunk_count} chunk{item.chunk_count === 1 ? "" : "s"}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </li>
  );
}
