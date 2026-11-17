import { CheckCircle2, Info, X, XCircle } from "lucide-react";
import type { Toast, ToastKind } from "./toastContext";

const STYLES: Record<ToastKind, { icon: typeof Info; iconClass: string; barClass: string }> = {
  success: { icon: CheckCircle2, iconClass: "text-emerald-500", barClass: "bg-emerald-500" },
  error: { icon: XCircle, iconClass: "text-red-500", barClass: "bg-red-500" },
  info: { icon: Info, iconClass: "text-violet-500", barClass: "bg-violet-500" },
};

interface ToastViewportProps {
  toasts: Toast[];
  onDismiss: (id: number) => void;
}

export function ToastViewport({ toasts, onDismiss }: ToastViewportProps) {
  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed inset-x-4 bottom-4 z-50 flex flex-col items-end gap-2 sm:inset-x-auto sm:right-6 sm:bottom-6"
    >
      {toasts.map((toast) => {
        const { icon: Icon, iconClass, barClass } = STYLES[toast.kind];
        return (
          <div
            key={toast.id}
            role={toast.kind === "error" ? "alert" : "status"}
            className="pointer-events-auto relative w-full overflow-hidden rounded-xl border border-slate-200 bg-white/95 shadow-lg shadow-slate-900/10 backdrop-blur animate-toast-in sm:w-96"
          >
            <span className={`absolute inset-y-0 left-0 w-1 ${barClass}`} />
            <div className="flex items-start gap-3 py-3 pl-4 pr-3">
              <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${iconClass}`} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-900">{toast.title}</p>
                {toast.message && <p className="mt-0.5 break-words text-[13px] text-slate-500">{toast.message}</p>}
              </div>
              <button
                onClick={() => onDismiss(toast.id)}
                className="rounded-md p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
                aria-label="Dismiss notification"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
