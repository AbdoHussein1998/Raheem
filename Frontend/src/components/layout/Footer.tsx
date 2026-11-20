import { BrandLogo } from "./BrandLogo";

export function Footer() {
  return (
    <footer className="theme-footer w-full bg-surface-container-lowest py-space-xl border-t border-surface-container-high/60 shadow-[0_-1px_8px_rgba(0,0,0,0.3)]">
      <div className="w-full px-margin flex items-center justify-center sm:justify-start gap-space-sm sm:gap-space-md">
        <BrandLogo className="h-9 sm:h-11 w-auto shrink-0 object-contain" />
        <span className="h-5 w-px shrink-0 bg-surface-variant" />
        <img
          src="/assets/sp-group-signature-white.webp"
          alt="Sun Pyramids Group"
          width={2440}
          height={477}
          className="h-11 sm:h-[52px] w-auto min-w-0 max-w-full object-contain"
        />
      </div>
    </footer>
  );
}
