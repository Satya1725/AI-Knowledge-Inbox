import { useCallback, useEffect, useRef, useState } from "react";
import { errorMessage } from "../api/client";
import { inboxApi } from "../api/inbox";
import type { IngestPayload, Item, ItemStatus } from "../api/types";

const POLL_INTERVAL_MS = 1500;

interface UseItemsOptions {
  /** Called once when an item goes from "processing" to "ready" or "failed". */
  onItemSettled?: (item: Item) => void;
}

/** Saved items + actions. Polls the server while any item is still being indexed. */
export function useItems({ onItemSettled }: UseItemsOptions = {}) {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Last known status per item, used to detect processing -> ready/failed transitions.
  const knownStatuses = useRef(new Map<string, ItemStatus>());
  // Keep the latest callback without re-creating `refresh` (which would restart polling).
  const onSettledRef = useRef(onItemSettled);
  onSettledRef.current = onItemSettled;

  const refresh = useCallback(async () => {
    try {
      const data = await inboxApi.listItems();

      for (const item of data.items) {
        const before = knownStatuses.current.get(item.id);
        if (before === "processing" && item.status !== "processing") {
          onSettledRef.current?.(item);
        }
      }
      knownStatuses.current = new Map(data.items.map((item) => [item.id, item.status]));

      setItems(data.items);
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const hasProcessing = items.some((item) => item.status === "processing");

  useEffect(() => {
    if (!hasProcessing) return;
    const timer = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [hasProcessing, refresh]);

  const addItem = useCallback(async (payload: IngestPayload): Promise<Item> => {
    const created = await inboxApi.ingest(payload);
    knownStatuses.current.set(created.id, created.status);
    setItems((prev) => [created, ...prev]);
    return created;
  }, []);

  const removeItem = useCallback(async (id: string) => {
    await inboxApi.deleteItem(id);
    knownStatuses.current.delete(id);
    setItems((prev) => prev.filter((item) => item.id !== id));
  }, []);

  return { items, loading, error, refresh, addItem, removeItem };
}
