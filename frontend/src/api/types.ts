// Mirrors backend/app/schemas.py

export type SourceType = "note" | "url";
export type ItemStatus = "processing" | "ready" | "failed";
export type ProviderName = "openai" | "gemini";

export interface Item {
  id: string;
  source_type: SourceType;
  title: string | null;
  url: string | null;
  preview: string | null;
  content_length: number | null;
  chunk_count: number;
  status: ItemStatus;
  error: string | null;
  created_at: string;
}

export type IngestPayload =
  | { type: "note"; text: string; title?: string }
  | { type: "url"; url: string; title?: string };

export interface QueryPayload {
  question: string;
  top_k?: number;
  provider?: ProviderName;
}

export interface Source {
  index: number;
  item_id: string;
  title: string | null;
  source_type: SourceType;
  url: string | null;
  snippet: string;
  score: number;
  cited: boolean;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  provider: ProviderName | null;
}

export interface ProvidersInfo {
  embedding_provider: ProviderName;
  default_chat_provider: ProviderName;
  available_chat_providers: ProviderName[];
}

export interface ApiErrorBody {
  error: { code: string; message: string; details?: { field: string; message: string }[] };
}
