import { useId } from "react";

/**
 * Inline SVG is essential here: animations declared in index.css cannot style
 * individual bulbs inside an external SVG loaded with <img src="...">.
 *
 * The garland geometry is preserved, while the circular bulbs are replaced
 * with candle-flame shapes. Each flame retains its original animation class.
 */
const BULBS = [
  { cx: 62, cy: 78, r: 5, color: "#f8be65" },
  { cx: 140, cy: 89, r: 5, color: "#65d1e8" },
  { cx: 218, cy: 99, r: 6, color: "#f8be65" },
  { cx: 309, cy: 117, r: 5, color: "#65d1e8" },
  { cx: 396, cy: 117, r: 5, color: "#f8be65" },
  { cx: 478, cy: 103, r: 5, color: "#65d1e8" },
  { cx: 92, cy: 60, r: 7, color: "#c44757" },
  { cx: 270, cy: 91, r: 7, color: "#c44757" },
] as const;

export function GarlandArtwork() {
  // Two mirrored garlands render simultaneously; SVG filter IDs must be unique.
  const glowId = useId();

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 500 176"
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
      className="w-full h-full"
    >
      <defs>
        {/* Soft glow surrounding each flame */}
        <filter id={glowId} x="-150%" y="-150%" width="400%" height="400%">
          <feGaussianBlur stdDeviation="3" />
        </filter>

        {/* Inner flame gradient for a warm, candle-like appearance */}
        <radialGradient id="garland-flame-gradient">
          <stop offset="0%" stopColor="#fff8d9" />
          <stop offset="35%" stopColor="#ffe49a" />
          <stop offset="75%" stopColor="#ffb347" />
          <stop offset="100%" stopColor="#ff8533" />
        </radialGradient>
      </defs>


      {/* Candle-flame bulbs */}
      {BULBS.map((bulb, index) => {
        const size = bulb.r * 1.5;

        return (
          <g
            key={`${bulb.cx}-${bulb.cy}`}
            className={`xmas-light-${(index % 5) + 1}`}
            style={{ color: bulb.color }}
          >
            {/* Colored ambient glow */}
            <ellipse
              cx={bulb.cx}
              cy={bulb.cy}
              rx={size * 1.8}
              ry={size * 2}
              fill={bulb.color}
              opacity="0.35"
              filter={`url(#${glowId})`}
            />

            {/* Outer flame silhouette */}
            <path
              d={`
                M ${bulb.cx} ${bulb.cy - size * 1.5}
                C ${bulb.cx + size * 0.15} ${bulb.cy - size * 0.9},
                  ${bulb.cx + size * 1.05} ${bulb.cy - size * 0.15},
                  ${bulb.cx + size * 0.8} ${bulb.cy + size * 0.55}
                C ${bulb.cx + size * 0.6} ${bulb.cy + size * 1.25},
                  ${bulb.cx - size * 0.6} ${bulb.cy + size * 1.25},
                  ${bulb.cx - size * 0.8} ${bulb.cy + size * 0.55}
                C ${bulb.cx - size * 1.05} ${bulb.cy - size * 0.15},
                  ${bulb.cx - size * 0.15} ${bulb.cy - size * 0.9},
                  ${bulb.cx} ${bulb.cy - size * 1.5}
                Z
              `}
              fill={bulb.color}
            />
          </g>
        );
      })}
    </svg>
  );
}
