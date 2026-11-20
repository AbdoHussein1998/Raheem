import { useCallback } from "react";

/** Browser fullscreen API and its user feedback are kept out of preview JSX. */
export function useFullscreenPreview(onNotice: (message: string) => void) {
  return useCallback(async (elementId: string) => {
    const target = document.getElementById(elementId);
    if (!target) {
      onNotice("Upload a photo to preview it.");
      return;
    }
    if (!target.requestFullscreen) {
      onNotice("Fullscreen preview is unavailable in this browser.");
      return;
    }
    try {
      await target.requestFullscreen();
    } catch {
      onNotice("Fullscreen preview could not be opened.");
    }
  }, [onNotice]);
}
