import type { SyntheticEvent } from "react";
import { BRAND_FALLBACK_URL, BRAND_LOGO_URL } from "../../constants/branding";

interface BrandLogoProps {
  className?: string;
}

export function BrandLogo({
  className = "h-6 w-auto object-contain",
}: BrandLogoProps) {
  const useFallback = (event: SyntheticEvent<HTMLImageElement>) => {
    if (event.currentTarget.src !== BRAND_FALLBACK_URL) {
      event.currentTarget.src = BRAND_FALLBACK_URL;
    }
  };

  return (
    <img
      src={BRAND_LOGO_URL}
      onError={useFallback}
      alt="Sun Pyramids Tours logo"
      className={className}
    />
  );
}
