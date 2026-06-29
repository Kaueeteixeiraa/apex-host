const tone: Record<string, string> = {
  online: "border-emerald-400/40 bg-emerald-400/10 text-emerald-200",
  offline: "border-slate-400/30 bg-slate-400/10 text-slate-200",
  building: "border-cyan-400/40 bg-cyan-400/10 text-cyan-200",
  error: "border-red-400/40 bg-red-400/10 text-red-200",
  paused: "border-amber-400/40 bg-amber-400/10 text-amber-200",
  success: "border-emerald-400/40 bg-emerald-400/10 text-emerald-200",
  failed: "border-red-400/40 bg-red-400/10 text-red-200",
  running: "border-cyan-400/40 bg-cyan-400/10 text-cyan-200",
  queued: "border-violet-400/40 bg-violet-400/10 text-violet-200",
  canceled: "border-slate-400/30 bg-slate-400/10 text-slate-200"
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex rounded-full border px-2 py-1 text-xs font-medium ${tone[status] || tone.offline}`}>
      {status}
    </span>
  );
}
