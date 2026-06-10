import { useId } from "react";

/**
 * Dashboard brand mark — lake surface (left) + Secchi disk (right).
 * Distinct from the Claro agent mascot.
 */
export function DashboardLogo({ className = "h-10 w-10", title = "Lake water clarity dashboard" }) {
  const diskClipId = useId();
  const leftClipId = useId();

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 200 200"
      className={className}
      role="img"
      aria-label={title}
    >
      <title>{title}</title>
      <defs>
        <clipPath id={diskClipId}>
          <circle cx="100" cy="100" r="71" />
        </clipPath>
        <clipPath id={leftClipId}>
          <rect x="0" y="0" width="100" height="200" />
        </clipPath>
      </defs>

      <circle cx="100" cy="100" r="94" fill="none" stroke="#005AB5" strokeWidth="12" />
      <circle cx="100" cy="100" r="84" fill="none" stroke="#FFFFFF" strokeWidth="2.5" />
      <circle cx="100" cy="100" r="78" fill="none" stroke="#005AB5" strokeWidth="10" />

      <g clipPath={`url(#${diskClipId})`}>
        <g clipPath={`url(#${leftClipId})`}>
          <rect x="0" y="0" width="100" height="200" fill="#FFFFFF" />
          <path
            d="M 29 100.5
               C 38 92, 44 108, 52 99.5
               C 60 91, 68 107, 76 99
               C 84 91, 92 105, 100 100
               L 100 171
               A 71 71 0 0 0 29 100.5
               Z"
            fill="#7EB8E8"
          />
        </g>

        <path d="M 100 29 A 71 71 0 0 1 171 100 L 100 100 Z" fill="#005AB5" />
        <path d="M 171 100 A 71 71 0 0 1 100 171 L 100 100 Z" fill="#FFFFFF" />

        <line x1="100" y1="29" x2="100" y2="171" stroke="#005AB5" strokeWidth="2.25" />
        <line x1="100" y1="100" x2="171" y2="100" stroke="#005AB5" strokeWidth="2.25" />
        <path
          d="M 29 100.5
             C 38 92, 44 108, 52 99.5
             C 60 91, 68 107, 76 99
             C 84 91, 92 105, 100 100"
          fill="none"
          stroke="#005AB5"
          strokeWidth="2.25"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
    </svg>
  );
}
