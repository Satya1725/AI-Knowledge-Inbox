import { useState, type FormEvent, type KeyboardEvent } from "react";
import { Link2, Loader2, Plus, StickyNote } from "lucide-react";
import { errorMessage } from "../api/client";
import type { IngestPayload } from "../api/types";
import { normalizeUrl } from "../utils/format";
import { Card } from "./ui/Card";
import { ErrorBanner } from "./ui/ErrorBanner";

type Mode = "note" | "url";

const MODES: { value: Mode; label: string; icon: typeof StickyNote }[] = [
  { value: "note", label: "Note", icon: StickyNote },
  { value: "url", label: "URL", icon: Link2 },
];

const inputClass =
  "w-full rounded-lg border border-slate-200 bg-slate-50/50 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 " +
  "focus:border-violet-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-violet-100 transition";

interface AddItemFormProps {
  onAdd: (payload: IngestPayload) => Promise<void>;
}

export function AddItemForm({ onAdd }: AddItemFormProps) {
  const [mode, setMode] = useState<Mode>("note");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = (mode === "note" ? text.trim() : url.trim()).length > 0 && !submitting;

  async function handleSubmit(event?: FormEvent) {
    event?.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setError(null);
    const optionalTitle = title.trim() || undefined;
    const payload: IngestPayload =
      mode === "note"
        ? { type: "note", text, title: optionalTitle }
        : { type: "url", url: normalizeUrl(url), title: optionalTitle };

    try {
      await onAdd(payload);
      setText("");
      setUrl("");
      setTitle("");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) handleSubmit();
  }

  return (
    <Card title="Add to inbox" subtitle="Notes and web pages become searchable" icon={<Plus className="h-4 w-4" />}>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-1 rounded-lg bg-slate-100 p-1">
          {MODES.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              type="button"
              onClick={() => {
                setMode(value);
                setError(null);
              }}
              className={`flex items-center justify-center gap-1.5 rounded-md py-1.5 text-sm font-medium transition ${
                mode === value ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>

        {mode === "note" ? (
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Paste or write anything worth remembering…"
            rows={5}
            className={`${inputClass} resize-y`}
          />
        ) : (
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/article"
            className={inputClass}
          />
        )}

        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={mode === "note" ? "Title (optional, defaults to first line)" : "Title (optional, defaults to page title)"}
          maxLength={200}
          className={inputClass}
        />

        {error && <ErrorBanner message={error} />}

        <button
          type="submit"
          disabled={!canSubmit}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          {submitting ? "Saving…" : mode === "note" ? "Save note" : "Save URL"}
        </button>
      </form>
    </Card>
  );
}
