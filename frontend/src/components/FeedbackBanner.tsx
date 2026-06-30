import { AlertTriangle, CheckCircle2, Info } from "lucide-react";

const tone = {
  success: "border-emerald-400/30 bg-emerald-400/10 text-emerald-100",
  error: "border-red-400/30 bg-red-400/10 text-red-100",
  info: "border-apex-cyan/30 bg-apex-cyan/10 text-apex-text"
};

const icons = {
  success: CheckCircle2,
  error: AlertTriangle,
  info: Info
};

export function FeedbackBanner({ type = "info", message }: { type?: keyof typeof tone; message: string }) {
  const Icon = icons[type];
  return (
    <div className={`flex items-start gap-3 rounded-md border p-3 text-sm ${tone[type]}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
