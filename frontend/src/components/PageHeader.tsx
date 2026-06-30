import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

export function PageHeader({
  title,
  eyebrow,
  description,
  icon: Icon,
  actions
}: {
  title: string;
  eyebrow?: string;
  description?: string;
  icon?: LucideIcon;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div className="flex items-start gap-3">
        {Icon ? (
          <div className="grid h-11 w-11 place-items-center rounded-lg border border-apex-cyan/40 bg-apex-cyan/10 text-apex-cyan shadow-glow">
            <Icon className="h-5 w-5" />
          </div>
        ) : null}
        <div>
          {eyebrow ? <div className="section-title mb-1">{eyebrow}</div> : null}
          <h1 className="page-title">{title}</h1>
          {description ? <p className="muted mt-1 max-w-2xl">{description}</p> : null}
        </div>
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}
