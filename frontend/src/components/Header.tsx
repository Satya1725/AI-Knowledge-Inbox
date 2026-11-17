import { Cpu, Inbox } from "lucide-react";
import type { ProvidersInfo } from "../api/types";
import { PROVIDER_LABELS } from "../utils/format";

export function Header({ providers }: { providers: ProvidersInfo | null }) {
  return (
    <header className="relative mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-6 sm:px-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-linear-to-br from-violet-500 to-indigo-600 text-white shadow-md shadow-violet-500/30">
          <Inbox className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-slate-900">Knowledge Inbox</h1>
          <p className="text-xs text-slate-500">Save notes and links. Ask questions. Get cited answers.</p>
        </div>
      </div>

      {providers && (
        <div className="hidden items-center gap-1.5 rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-xs text-slate-600 shadow-sm backdrop-blur sm:flex">
          <Cpu className="h-3.5 w-3.5 text-violet-500" />
          Embeddings: <span className="font-medium text-slate-800">{PROVIDER_LABELS[providers.embedding_provider]}</span>
        </div>
      )}
    </header>
  );
}
