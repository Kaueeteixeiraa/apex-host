import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="panel grid place-items-center p-8 text-center">
      <div className="grid h-14 w-14 place-items-center rounded-lg border border-apex-cyan/30 bg-apex-cyan/10 text-apex-cyan">
        <Icon className="h-6 w-6" />
      </div>
      <h2 className="mt-4 font-semibold text-white">{title}</h2>
      <p className="muted mt-1 max-w-md">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
