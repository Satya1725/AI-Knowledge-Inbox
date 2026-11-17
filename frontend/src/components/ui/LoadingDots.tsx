/** Three bouncing dots: the "thinking" indicator. */
export function LoadingDots({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 ${className}`} aria-label="Loading">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="h-2 w-2 animate-bounce rounded-full bg-linear-to-br from-violet-500 to-indigo-500"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  );
}
