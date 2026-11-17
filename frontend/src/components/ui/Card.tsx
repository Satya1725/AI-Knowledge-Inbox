import type { ReactNode } from "react";

interface CardProps {
  title?: string;
  subtitle?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
  /** Extra classes for the body, e.g. to make it a flex column with an inner scroll area. */
  bodyClassName?: string;
  children: ReactNode;
}

export function Card({ title, subtitle, icon, action, className = "", bodyClassName = "", children }: CardProps) {
  return (
    <section
      className={`flex flex-col rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50 ${className}`}
    >
      {title && (
        <header className="flex shrink-0 items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <div className="flex items-center gap-3">
            {icon && (
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                {icon}
              </span>
            )}
            <div>
              <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
              {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
            </div>
          </div>
          {action}
        </header>
      )}
      <div className={`min-h-0 flex-1 p-5 ${bodyClassName}`}>{children}</div>
    </section>
  );
}
