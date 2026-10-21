export default function Hero() {
  return (
    <section className="w-full bg-surface-container-lowest rounded-2xl p-space-md lg:p-space-lg shadow-[0_4px_28px_-6px_rgba(15,56,44,0.06)] border border-surface-container-high/80 relative overflow-hidden mb-space-xl text-center">
      <div className="absolute -left-14 -bottom-14 opacity-[0.04] pointer-events-none text-primary">
        <svg className="w-72 h-72" fill="currentColor" viewBox="0 0 100 100">
          <polygon points="50 0, 61 38, 98 35, 68 59, 79 96, 50 72, 21 96, 32 59, 2 35, 39 38"></polygon>
          <circle
            cx="50"
            cy="50"
            fill="none"
            r="28"
            stroke="currentColor"
            strokeWidth="3"
          ></circle>
        </svg>
      </div>
      <div className="absolute -right-14 -top-14 opacity-[0.04] pointer-events-none text-primary">
        <svg className="w-72 h-72" fill="currentColor" viewBox="0 0 100 100">
          <polygon points="50 0, 61 38, 98 35, 68 59, 79 96, 50 72, 21 96, 32 59, 2 35, 39 38"></polygon>
        </svg>
      </div>
      <div className="max-w-3xl mx-auto flex flex-col items-center relative z-10">
        <div>
          <h1 className="font-display-lg text-display-lg-mobile md:text-display-lg text-primary tracking-tight mb-space-xs font-bold">
            بكل رحمة و حب نقدم لكم رحيم
          </h1>

          <blockquote className="font-scripture-quote text-scripture-quote-mobile md:text-scripture-quote text-secondary italic mb-space-sm max-w-2xl leading-relaxed">
            {" "}
            ليكون لك مشروع دعوة{" "}
          </blockquote>
        </div>
      </div>
    </section>
  );
}
