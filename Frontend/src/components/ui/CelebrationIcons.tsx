import type { SVGProps } from "react";

/**
 * Christmas Tree icon with star topper, tiered branches, decorative garlands, and trunk.
 */
export function ChristmasTreeIcon({ className = "w-5 h-5", ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      {/* Star topper */}
      <path
        fill="currentColor"
        stroke="none"
        d="M12 1.8l.9 1.8 2 .3-1.4 1.4.3 2L12 6.4 10.2 7.3l.3-2-1.4-1.4 2-.3.9-1.8z"
      />
      {/* Tiered tree outline */}
      <path d="M12 6.5L8.5 10.5h2L7 14.5h2.5L5.5 19h13L14.5 14.5h2.5L13.5 10.5h2L12 6.5z" />
      {/* Festive garland curve */}
      <path d="M9.5 12c1.5 1 3.5 1 5 0" />
      <path d="M8 16.5c2.5 1.5 5.5 1.5 8 0" />
      {/* Trunk */}
      <path d="M10.5 19v3h3v-3" />
    </svg>
  );
}

/**
 * Ancient Egyptian Pharaonic Mask (Tutankhamun death mask)
 * with Nemes headdress, sacred Uraeus (cobra), headdress stripes, and royal braided beard.
 */
export function PharaonicMaskIcon({ className = "w-5 h-5", ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      {/* Sacred Uraeus (Cobra emblem on forehead) */}
      <path
        d="M12 1.3c-.7 0-1.1.4-1.1.9 0 .4.3.7.7.8v.8h.8v-.8c.4-.1.7-.4.7-.8 0-.5-.4-.9-1.1-.9z"
        fill="currentColor"
        stroke="none"
      />

      {/* Nemes outer headdress dome & wings */}
      <path d="M7 6.5C7 3.8 9.2 2.2 12 2.2s5 1.6 5 4.3l3 3.5c.6.7.7 1.6.4 2.5l-1.9 6.5c-.2.7-.8 1.2-1.5 1.2h-.8l1-6.2-.6-7.5" />
      <path d="M17 6.5L7 6.5l-3 3.5c-.6.7-.7 1.6-.4 2.5l1.9 6.5c.2.7.8 1.2 1.5 1.2h.8l-1-6.2.6-7.5" />

      {/* Brow Headband */}
      <path d="M7 7.5h10" />

      {/* Nemes headdress stripes */}
      <path d="M5.5 10.5h1.5M17 10.5h1.5" />
      <path d="M6 13.5h1.5M16.5 13.5h1.5" />
      <path d="M6.8 16.5h1.2M16 16.5h1.2" />

      {/* Face contour */}
      <path d="M8.5 8.5h7l-.7 5.5c-.2 1.3-1.3 2.2-2.8 2.2s-2.6-.9-2.8-2.2l-.7-5.5z" />

      {/* Egyptian almond eyes */}
      <path d="M9.8 11.2c.4-.3.9-.3 1.3 0M12.9 11.2c.4-.3.9-.3 1.3 0" />

      {/* Royal braided beard */}
      <path d="M10.8 16.5v4.5c0 .4.4.8.8.8h.8c.4 0 .8-.4.8-.8v-4.5" />
      <path d="M10.8 18.5h2.4M10.8 20.3h2.4" />
    </svg>
  );
}
