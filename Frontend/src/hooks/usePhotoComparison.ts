import { useState } from "react";

export type PreviewMode = "side" | "compare";

/** Manages the before/after preview mode and slider position. */
export function usePhotoComparison(resultUrl: string | null) {
  const [mode, setMode] = useState<PreviewMode>("side");
  const [position, setPosition] = useState(50);
  // Keep the original preference while hiding Compare until a result exists.
  const view: PreviewMode = resultUrl ? mode : "side";

  return { view, position, setMode, setPosition };
}
