import { useCallback, useRef, useState } from "react";
import { errorMessage } from "../api/client";
import { inboxApi } from "../api/inbox";
import type { ProviderName, QueryResponse } from "../api/types";

/** State for one question/answer round trip. Ignores responses to superseded questions. */
export function useAsk() {
  const [question, setQuestion] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const latestRequest = useRef(0);

  const ask = useCallback(async (text: string, provider?: ProviderName) => {
    const requestId = ++latestRequest.current;
    setQuestion(text);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await inboxApi.query({ question: text, provider });
      if (requestId === latestRequest.current) setResult(response);
    } catch (err) {
      if (requestId === latestRequest.current) setError(errorMessage(err));
    } finally {
      if (requestId === latestRequest.current) setLoading(false);
    }
  }, []);

  return { question, result, loading, error, ask };
}
