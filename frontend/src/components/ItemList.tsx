import { useCallback, useMemo, useState } from "react";
import { Library, Search } from "lucide-react";
import type { Item } from "../api/types";
import { Card } from "./ui/Card";
import { ConfirmDialog } from "./ui/ConfirmDialog";
import { ErrorBanner } from "./ui/ErrorBanner";
import { ItemCard, itemDisplayTitle, ItemTypeIcon } from "./ItemCard";

interface ItemListProps {
  items: Item[];
  loading: boolean;
  error: string | null;
  onDelete: (id: string) => Promise<void>;
}

export function ItemList({ items, loading, error, onDelete }: ItemListProps) {
  const [filter, setFilter] = useState("");

  const visibleItems = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((item) =>
      [item.title, item.url, item.preview].some((field) => field?.toLowerCase().includes(needle)),
    );
  }, [items, filter]);

  // Delete confirmation. `pendingDelete` is kept after closing so the dialog
  // still has content to show while its exit animation plays.
  const [pendingDelete, setPendingDelete] = useState<Item | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const requestDelete = useCallback((item: Item) => {
    setPendingDelete(item);
    setConfirmOpen(true);
  }, []);

  const cancelDelete = useCallback(() => setConfirmOpen(false), []);

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await onDelete(pendingDelete.id);
    } catch {
      // The caller already shows an error toast.
    } finally {
      setDeleting(false);
      setConfirmOpen(false);
    }
  }

  return (
    <Card
      title="Library"
      subtitle={`${items.length} saved item${items.length === 1 ? "" : "s"}`}
      icon={<Library className="h-4 w-4" />}
    >
      {items.length > 3 && (
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter by title or content"
            className="w-full rounded-lg border border-slate-200 py-2 pl-9 pr-3 text-sm placeholder:text-slate-400 focus:border-violet-400 focus:outline-none focus:ring-4 focus:ring-violet-100"
          />
        </div>
      )}

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <ItemListSkeleton />
      ) : items.length === 0 ? (
        <p className="py-10 text-center text-sm text-slate-400">
          Nothing saved yet. Add a note or URL above to get started.
        </p>
      ) : visibleItems.length === 0 ? (
        <p className="py-6 text-center text-sm text-slate-400">No items match “{filter}”.</p>
      ) : (
        <ul className="scroll-thin -mr-2 max-h-130 space-y-2 overflow-y-auto pr-2">
          {visibleItems.map((item) => (
            <ItemCard
              key={item.id}
              item={item}
              onRequestDelete={requestDelete}
              deleting={deleting && pendingDelete?.id === item.id}
            />
          ))}
        </ul>
      )}

      <ConfirmDialog
        open={confirmOpen}
        busy={deleting}
        title={pendingDelete?.source_type === "url" ? "Delete this link?" : "Delete this note?"}
        description="It will be removed from your Library and won't be used to answer questions anymore. This can't be undone."
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
      >
        {pendingDelete && (
          <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5">
            <ItemTypeIcon item={pendingDelete} />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-800">{itemDisplayTitle(pendingDelete)}</p>
              {pendingDelete.status === "ready" && (
                <p className="text-xs text-slate-400">
                  {pendingDelete.chunk_count} indexed chunk{pendingDelete.chunk_count === 1 ? "" : "s"}
                </p>
              )}
            </div>
          </div>
        )}
      </ConfirmDialog>
    </Card>
  );
}

function ItemListSkeleton() {
  return (
    <ul className="space-y-2" aria-label="Loading library">
      {[0, 1, 2].map((i) => (
        <li key={i} className="flex animate-pulse gap-3 rounded-xl border border-slate-100 p-3.5">
          <div className="h-8 w-8 shrink-0 rounded-lg bg-slate-100" />
          <div className="flex-1 space-y-2 py-0.5">
            <div className="h-3 w-2/3 rounded bg-slate-200" />
            <div className="h-2.5 w-full rounded bg-slate-100" />
            <div className="h-2.5 w-1/3 rounded bg-slate-100" />
          </div>
        </li>
      ))}
    </ul>
  );
}
