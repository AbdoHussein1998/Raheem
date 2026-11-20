import { GarlandArtwork } from "./GarlandArtwork";

/** Keep the original garland positioning and right-hand mirroring. */
export function FestiveGarlands() {
  return (
    <div className="fixed top-0 left-0 right-0 pointer-events-none z-[60] overflow-hidden h-44" aria-hidden="true">
      <div className="absolute top-0 left-0 w-[420px] sm:w-[500px] h-44">
        <GarlandArtwork />
      </div>
      <div className="absolute top-0 right-0 w-[420px] sm:w-[500px] h-44 scale-x-[-1]">
        <GarlandArtwork />
      </div>
    </div>
  );
}
