export function Header() {
  return (
    <header className="theme-header fixed top-0 left-0 right-0 z-50 bg-surface-container-lowest/90 backdrop-blur-xl border-b border-surface-container-high/60 shadow-[0_1px_8px_rgba(0,0,0,0.4)]">
      <div className="h-20 sm:h-24 w-full px-margin flex items-center">
        <img
          src="/assets/sp-group-signature-white.webp"
          alt="Sun Pyramids Group"
          width={2440}
          height={477}
          className="h-8 sm:h-10 w-auto object-contain shrink-0"
        />
      </div>
    </header>
  );
}
