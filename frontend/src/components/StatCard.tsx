import { LucideIcon } from "lucide-react";

export function StatCard({
  title,
  value,
  icon: Icon,
  detail
}: {
  title: string;
  value: string | number;
  icon: LucideIcon;
  detail?: string;
}) {
  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-apex-muted">{title}</span>
        <Icon className="h-5 w-5 text-apex-cyan" />
      </div>
      <div className="mt-4 text-3xl font-semibold text-white">{value}</div>
      {detail ? <div className="mt-2 text-xs text-apex-muted">{detail}</div> : null}
    </div>
  );
}
