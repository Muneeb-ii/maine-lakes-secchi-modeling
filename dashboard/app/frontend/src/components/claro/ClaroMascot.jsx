import { useId } from "react";

/** Secchi disk with a friendly face — Claro’s identity mark. */
export function ClaroMascot({ className = "h-5 w-5" }) {
  const clipId = useId();
  const cx = 16;
  const cy = 17.5;
  const r = 11;

  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden
    >
      <defs>
        <clipPath id={clipId}>
          <circle cx={cx} cy={cy} r={r} />
        </clipPath>
      </defs>

      <path
        d="M13.5 3.5c0-1 1.2-1.8 2.5-1.8s2.5.8 2.5 1.8v1.2h-5V3.5z"
        fill="#1A9B6E"
        stroke="#0F6B4A"
        strokeWidth="0.75"
      />
      <circle cx={cx} cy={3.8} r="1.1" fill="none" stroke="#0F6B4A" strokeWidth="1" />

      <circle cx={cx} cy={cy} r={r + 0.75} stroke="#0F6B4A" strokeWidth="1.25" fill="white" />

      <g clipPath={`url(#${clipId})`}>
        <path
          d={`M ${cx} ${cy} L ${cx} ${cy - r} A ${r} ${r} 0 0 0 ${cx - r} ${cy} Z`}
          fill="#1A9B6E"
        />
        <path
          d={`M ${cx} ${cy} L ${cx} ${cy - r} A ${r} ${r} 0 0 1 ${cx + r} ${cy} Z`}
          fill="#FFFFFF"
        />
        <path
          d={`M ${cx} ${cy} L ${cx + r} ${cy} A ${r} ${r} 0 0 1 ${cx} ${cy + r} Z`}
          fill="#3ECF8E"
        />
        <path
          d={`M ${cx} ${cy} L ${cx} ${cy + r} A ${r} ${r} 0 0 0 ${cx - r} ${cy} Z`}
          fill="#1A9B6E"
        />
        <path d={`M ${cx} ${cy - r} L ${cx} ${cy + r}`} stroke="#0F6B4A" strokeWidth="0.85" opacity="0.35" />
        <path d={`M ${cx - r} ${cy} L ${cx + r} ${cy}`} stroke="#0F6B4A" strokeWidth="0.85" opacity="0.35" />
      </g>

      <circle cx={19.2} cy={13.8} r="0.95" fill="#0F6B4A" />
      <circle cx={22.2} cy={13.8} r="0.95" fill="#0F6B4A" />
      <path
        d="M18.8 16.2c.9 1 1.8 1.45 2.8 1.45s1.9-.45 2.8-1.45"
        stroke="#0F6B4A"
        strokeWidth="1.1"
        strokeLinecap="round"
      />
    </svg>
  );
}
