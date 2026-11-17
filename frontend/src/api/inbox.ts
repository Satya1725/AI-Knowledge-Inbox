import { request } from "./client";
import type { IngestPayload, Item, ProvidersInfo, QueryPayload, QueryResponse } from "./types";

export const inboxApi = {
  ingest: (payload: IngestPayload) => request<Item>("/ingest", { method: "POST", body: payload }),

  listItems: () => request<{ items: Item[] }>("/items"),

  deleteItem: (id: string) => request<void>(`/items/${id}`, { method: "DELETE" }),

  reindexItem: (id: string) => request<Item>(`/items/${id}/reindex`, { method: "POST" }),

  query: (payload: QueryPayload) => request<QueryResponse>("/query", { method: "POST", body: payload }),

  providers: () => request<ProvidersInfo>("/providers"),
};
