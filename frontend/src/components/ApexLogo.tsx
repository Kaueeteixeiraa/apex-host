type ApexLogoProps = {
  className?: string;
  animated?: boolean;
};

export function ApexLogo({ className = "h-12 w-12", animated = false }: ApexLogoProps) {
  return (
    <svg viewBox="0 0 120 120" className={`${className} ${animated ? "apex-pulse" : ""}`} role="img" aria-label="Apex Host">
      <defs>
        <linearGradient id="apexLogoGlow" x1="28" x2="92" y1="18" y2="102" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7ddcff" />
          <stop offset="0.48" stopColor="#18b6ff" />
          <stop offset="1" stopColor="#006dff" />
        </linearGradient>
        <filter id="apexLogoShadow" x="-40%" y="-40%" width="180%" height="180%">
          <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#18b6ff" floodOpacity="0.75" />
        </filter>
      </defs>
      <path
        d="M60 8 103 33v54l-43 25-43-25V33L60 8Z"
        fill="rgba(3,16,35,0.82)"
        stroke="url(#apexLogoGlow)"
        strokeWidth="3"
        filter="url(#apexLogoShadow)"
      />
      <path
        d="M60 27 88 89H73l-5-12H45l-10 12H20L60 27Zm0 25L49 67h15l-4-15Z"
        fill="none"
        stroke="url(#apexLogoGlow)"
        strokeWidth="7"
        strokeLinejoin="round"
        strokeLinecap="round"
        filter="url(#apexLogoShadow)"
      />
      <path d="M42 83 72 72l12 17" fill="none" stroke="#d8f5ff" strokeWidth="4" strokeLinecap="round" opacity="0.82" />
    </svg>
  );
}
