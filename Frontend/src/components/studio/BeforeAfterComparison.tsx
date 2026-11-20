import { MaterialIcon } from "../ui/MaterialIcon";

interface Props {
  photoUrl: string;
  resultUrl: string;
  position: number;
  onPositionChange: (position: number) => void;
}

/** Pure before/after comparison UI: its range input is still the drag handle. */
export function BeforeAfterComparison({ photoUrl, resultUrl, position, onPositionChange }: Props) {
  return (
    <div className="flex flex-col gap-space-xs bg-surface-container rounded-xl p-space-sm shadow-md border border-surface-container-high">
        <div className="flex items-center justify-between px-space-xs py-1 gap-2 flex-wrap">
          <span className="text-label-sm font-label-sm text-on-surface uppercase tracking-wider font-semibold">Interactive Before & After Comparison</span>
          <span className="text-label-sm font-label-sm text-secondary">Drag handle to compare</span>
        </div>
        <div id="comparison-preview" className="relative w-full aspect-square rounded-lg overflow-hidden bg-surface-container-lowest select-none border border-surface-container">
          <img src={resultUrl} alt="Styled after" className="absolute inset-0 w-full h-full object-contain pointer-events-none" />
          <img src={photoUrl} alt="Original before" className="absolute inset-0 w-full h-full object-contain pointer-events-none" style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }} />
          <div className="absolute top-3 left-3 px-space-xs py-0.5 rounded bg-surface-container-lowest/80 text-on-surface-variant font-label-sm text-label-sm font-bold pointer-events-none">BEFORE</div>
          <div className="absolute top-3 right-3 px-space-xs py-0.5 rounded bg-surface-container-lowest/80 text-primary font-label-sm text-label-sm pointer-events-none font-bold">AFTER</div>
          <div className="absolute top-0 bottom-0 z-20 flex items-center justify-center pointer-events-none border-l-2 border-secondary" style={{ left: `${position}%` }}>
            <div className="w-8 h-8 rounded-full bg-primary text-on-primary flex items-center justify-center shadow-[0_0_16px_rgba(245,158,11,0.8)] border border-primary-fixed"><MaterialIcon name="compare_arrows" className="text-title-sm" /></div>
          </div>
          <input
            className="absolute inset-0 opacity-0 cursor-ew-resize w-full h-full z-30 m-0"
            id="split-range-input" type="range" min={0} max={100} value={position}
            aria-label="Before and after comparison percentage"
            onChange={event => onPositionChange(Number(event.target.value))}
          />
        </div>
    </div>
  );
}
