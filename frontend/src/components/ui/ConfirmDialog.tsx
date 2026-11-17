import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { AlertTriangle, Loader2 } from "lucide-react";

const EXIT_ANIMATION_MS = 160;

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  /** Shows a spinner on the confirm button and blocks closing while true. */
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  children?: ReactNode;
}

/**
 * Animated confirmation modal (for destructive actions).
 * Rendered in a portal so parent transforms/overflow can't clip it.
 * Closes on Esc or backdrop click; keeps itself mounted briefly so the exit animation can play.
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Delete",
  cancelLabel = "Cancel",
  busy = false,
  onConfirm,
  onCancel,
  children,
}: ConfirmDialogProps) {
  const [mounted, setMounted] = useState(open);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);

  // Mount immediately on open; on close, wait for the exit animation before unmounting.
  useEffect(() => {
    if (open) {
      setMounted(true);
      return;
    }
    const timer = setTimeout(() => setMounted(false), EXIT_ANIMATION_MS);
    return () => clearTimeout(timer);
  }, [open]);

  // Esc to cancel, lock page scroll, focus the safe option.
  useEffect(() => {
    if (!open) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !busy) onCancel();
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleKeyDown);
    cancelButtonRef.current?.focus();

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, busy, onCancel]);

  if (!mounted) return null;

  const closing = !open;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className={`absolute inset-0 bg-slate-900/40 backdrop-blur-sm ${closing ? "animate-overlay-out" : "animate-overlay-in"}`}
        onClick={() => !busy && onCancel()}
      />

      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        className={`relative w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl shadow-slate-900/20 ring-1 ring-slate-200 ${
          closing ? "animate-modal-out" : "animate-modal-in"
        }`}
      >
        <div className="flex gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-red-50 ring-8 ring-red-50/50">
            <AlertTriangle className="h-5 w-5 text-red-600" />
          </span>
          <div className="min-w-0 flex-1 pt-0.5">
            <h2 id="confirm-dialog-title" className="text-base font-semibold text-slate-900">
              {title}
            </h2>
            {description && <p className="mt-1 text-sm leading-relaxed text-slate-500">{description}</p>}
          </div>
        </div>

        {children && <div className="mt-4">{children}</div>}

        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            ref={cancelButtonRef}
            onClick={onCancel}
            disabled={busy}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-100 disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm shadow-red-600/30 transition hover:bg-red-700 focus:outline-none focus:ring-4 focus:ring-red-100 disabled:opacity-70"
          >
            {busy && <Loader2 className="h-4 w-4 animate-spin" />}
            {busy ? "Deleting…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
