import { useCallback, useMemo, useState, type ReactNode } from "react";
import { ToastContext, type Toast, type ToastApi, type ToastKind } from "./toastContext";
import { ToastViewport } from "./ToastViewport";

const MAX_VISIBLE = 4;
const DURATION_MS: Record<ToastKind, number> = { success: 4000, info: 4000, error: 7000 };

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((t) => t.id !== id));
  }, []);

  const show = useCallback(
    (kind: ToastKind, title: string, message?: string) => {
      const id = ++nextId;
      setToasts((current) => [...current.slice(-(MAX_VISIBLE - 1)), { id, kind, title, message }]);
      setTimeout(() => dismiss(id), DURATION_MS[kind]);
    },
    [dismiss],
  );

  const api = useMemo<ToastApi>(
    () => ({
      success: (title, message) => show("success", title, message),
      error: (title, message) => show("error", title, message),
      info: (title, message) => show("info", title, message),
    }),
    [show],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}
