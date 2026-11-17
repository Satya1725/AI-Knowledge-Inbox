import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import type { ItemStatus } from "../api/types";

const STYLES: Record<ItemStatus, { label: string; className: string; icon: typeof CheckCircle2 }> = {
  processing: { label: "Indexing", className: "bg-amber-50 text-amber-700 ring-amber-200", icon: Loader2 },
  ready: { label: "Ready", className: "bg-emerald-50 text-emerald-700 ring-emerald-200", icon: CheckCircle2 },
  failed: { label: "Failed", className: "bg-red-50 text-red-700 ring-red-200", icon: XCircle },
};

export function StatusBadge({ status }: { status: ItemStatus }) {
  const { label, className, icon: Icon } = STYLES[status];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${className}`}>
      <Icon className={`h-3 w-3 ${status === "processing" ? "animate-spin" : ""}`} />
      {label}
    </span>
  );
}
