import { useEffect, useState } from "react";
import { inboxApi } from "../api/inbox";
import type { ProvidersInfo } from "../api/types";

export function useProviders() {
  const [providers, setProviders] = useState<ProvidersInfo | null>(null);

  useEffect(() => {
    inboxApi
      .providers()
      .then(setProviders)
      .catch(() => setProviders(null)); // non-critical: the UI just hides the provider switch
  }, []);

  return providers;
}
