import { useId } from "react";

type ApexLogoProps = {
  className?: string;
  animated?: boolean;
  size?: number | "sm" | "md" | "lg" | "xl";
  collapsed?: boolean;
  showText?: boolean;
};

const sizeClass = {
  sm: "h-9 w-9",
  md: "h-12 w-12",
  lg: "h-16 w-16",
  xl: "h-24 w-24"
};

export function ApexLogo({ className, animated = false, size = "md", collapsed = false, showText = false }: ApexLogoProps) {
  const reactId = useId().replace(/:/g, "");
  const gradientId = `apexLogoGlow-${reactId}`;
  const filterId = `apexLogoShadow-${reactId}`;
  const iconClass = className || (typeof size === "number" ? "" : sizeClass[size]);
  const iconStyle = typeof size === "number" ? { width: size, height: size } : undefined;
  const icon = (
    <svg viewBox="0 0 120 120" className={`${iconClass} shrink-0 ${animated ? "apex-pulse" : ""}`} style={iconStyle} role="img" aria-label="Apex Host">
      <defs>
        <linearGradient id={gradientId} x1="28" x2="92" y1="18" y2="102" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7ddcff" />
          <stop offset="0.48" stopColor="#18b6ff" />
          <stop offset="1" stopColor="#006dff" />
        </linearGradient>
        <filter id={filterId} x="-40%" y="-40%" width="180%" height="180%">
          <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#18b6ff" floodOpacity="0.75" />
        </filter>
      </defs>
      <path
        d="M60 8 103 33v54l-43 25-43-25V33L60 8Z"
        fill="rgba(3,16,35,0.82)"
        stroke={`url(#${gradientId})`}
        strokeWidth="3"
        filter={`url(#${filterId})`}
      />
      <path
        d="M60 27 88 89H73l-5-12H45l-10 12H20L60 27Zm0 25L49 67h15l-4-15Z"
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth="7"
        strokeLinejoin="round"
        strokeLinecap="round"
        filter={`url(#${filterId})`}
      />
      <path d="M42 83 72 72l12 17" fill="none" stroke="#d8f5ff" strokeWidth="4" strokeLinecap="round" opacity="0.82" />
    </svg>
  );

  if (!showText || collapsed) return icon;

  return (
    <div className="flex min-w-0 items-center gap-3">
      {icon}
      <div className="min-w-0">
        <div className="truncate font-semibold text-white">Apex Host</div>
        <div className="truncate text-xs text-apex-muted">Infraestrutura privada Apex</div>
      </div>
    </div>
  );
}
