import { useCallback } from "react";
import { errorMessage } from "./api/client";
import type { IngestPayload, Item } from "./api/types";
import { AddItemForm } from "./components/AddItemForm";
import { AskPanel } from "./components/AskPanel";
import { Header } from "./components/Header";
import { ItemList } from "./components/ItemList";
import { useToast } from "./components/toast/toastContext";
import { useItems } from "./hooks/useItems";
import { useProviders } from "./hooks/useProviders";
import { hostname } from "./utils/format";

function displayName(item: Item): string {
  return item.title || hostname(item.url) || "Untitled";
}

export default function App() {
  const toast = useToast();

  const handleItemSettled = useCallback(
    (item: Item) => {
      if (item.status === "ready") {
        toast.success(
          `"${displayName(item)}" is ready`,
          `Indexed into ${item.chunk_count} chunk${item.chunk_count === 1 ? "" : "s"}. You can ask about it now.`,
        );
      } else {
        toast.error(`Couldn't index "${displayName(item)}"`, item.error ?? undefined);
      }
    },
    [toast],
  );

  const { items, loading, error, addItem, removeItem, reindexItem } = useItems({ onItemSettled: handleItemSettled });
  const providers = useProviders();
  const readyItemCount = items.filter((item) => item.status === "ready").length;

  // Errors from addItem are re-thrown so the form can show them inline as well.
  const handleAdd = useCallback(
    async (payload: IngestPayload) => {
      await addItem(payload);
      toast.info(
        payload.type === "note" ? "Note saved to Library" : "URL saved to Library",
        payload.type === "note" ? "Indexing it now…" : "Fetching the page and indexing it…",
      );
    },
    [addItem, toast],
  );

  const handleDelete = useCallback(
    async (id: string) => {
      const item = items.find((i) => i.id === id);
      try {
        await removeItem(id);
        toast.success("Item deleted", item ? `"${displayName(item)}" was removed from your Library.` : undefined);
      } catch (err) {
        toast.error("Couldn't delete item", errorMessage(err));
        throw err;
      }
    },
    [items, removeItem, toast],
  );

  const handleReindex = useCallback(
    async (item: Item) => {
      try {
        await reindexItem(item.id);
        toast.info(
          `Re-indexing "${displayName(item)}"`,
          item.source_type === "url" ? "Fetching the latest version of the page…" : "Rebuilding its chunks…",
        );
      } catch (err) {
        toast.error("Couldn't re-index item", errorMessage(err));
      }
    },
    [reindexItem, toast],
  );

  return (
    // On large screens the app fills exactly one viewport: the page itself never scrolls,
    // only the Library list and the answer area do. On small screens it falls back to normal page scroll.
    <div className="relative flex min-h-screen flex-col lg:h-screen lg:overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-80 bg-linear-to-b from-emerald-50 via-teal-50/40 to-transparent" />

      <Header providers={providers} />

      <main className="relative mx-auto grid w-full max-w-7xl flex-1 gap-6 px-4 pb-6 sm:px-6 lg:min-h-0 lg:grid-cols-[minmax(0,400px)_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)]">
        <div className="scroll-thin flex flex-col gap-6 lg:-mr-2 lg:min-h-0 lg:overflow-y-auto lg:pr-2">
          <AddItemForm onAdd={handleAdd} />
          <ItemList items={items} loading={loading} error={error} onDelete={handleDelete} onReindex={handleReindex} />
        </div>

        <AskPanel providers={providers} readyItemCount={readyItemCount} />
      </main>
    </div>
  );
}
