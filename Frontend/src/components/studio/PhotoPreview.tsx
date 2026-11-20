import { usePhotoComparison } from "../../hooks/usePhotoComparison";
import { useFullscreenPreview } from "../../hooks/useFullscreenPreview";
import { BeforeAfterComparison } from "./BeforeAfterComparison";
import { MaterialIcon } from "../ui/MaterialIcon";
import type { SourcePhoto } from "../../types/studio";

interface Props {
  photo: SourcePhoto | null;
  resultUrl: string | null;
  generating: boolean;
  onReset: () => void;
  onNotice: (message: string) => void;
}

/**
 * PREVIEW DIMENSIONS ARE INTENTIONAL: the existing aspect-square containers,
 * object-contain sizing, and comparison layout must remain unchanged.
 * These are browser display sizes, not the backend mockup image dimensions.
 */
export function PhotoPreview({ photo, resultUrl, generating, onReset, onNotice }: Props) {
  const { view, position, setMode, setPosition } = usePhotoComparison(resultUrl);

  const requestFullscreen = useFullscreenPreview(onNotice);
  const openFullscreen = () => {
    if (!photo) {
      onNotice("Upload a photo to preview it.");
      return;
    }
    const targetId = view === "compare" ? "comparison-preview" : resultUrl ? "styled-preview" : "original-preview";
    void requestFullscreen(targetId);
  };

  return (
    <>
      <div className="flex items-center justify-between gap-space-sm flex-wrap" aria-label="Preview display mode">
        <div className="flex items-center gap-space-xs rounded-lg bg-surface-container-low p-1" role="group" aria-label="Preview mode">
          <button
            type="button" aria-pressed={view === "side"} onClick={() => setMode("side")}
            className={`px-space-md py-space-xs rounded-lg text-title-sm font-title-sm flex items-center gap-1 transition-colors ${view === "side" ? "bg-surface-container-high text-primary shadow-sm" : "text-on-surface-variant hover:text-on-surface"}`}
          ><MaterialIcon name="view_column" className="text-title-sm" /> Side by side</button>
          <button
            type="button" aria-pressed={view === "compare"} onClick={() => resultUrl ? setMode("compare") : onNotice("Generate a photo before comparing the results.")}
            className={`px-space-md py-space-xs rounded-lg text-title-sm font-title-sm flex items-center gap-1 transition-colors ${view === "compare" ? "bg-surface-container-high text-secondary shadow-sm" : "text-on-surface-variant hover:text-on-surface"}`}
          ><MaterialIcon name="compare" className="text-title-sm" /> Compare</button>
        </div>
        <div className="flex gap-space-xs">
          <button type="button" onClick={openFullscreen} className="text-label-sm text-on-surface-variant hover:text-secondary rounded-md px-space-xs py-space-xs" title="Expand photo" aria-label="Expand photo"><MaterialIcon name="fullscreen" className="align-middle" /></button>
          <button type="button" onClick={onReset} className="text-label-sm text-on-surface-variant hover:text-error rounded-md px-space-xs py-space-xs" title="Reset photo" aria-label="Reset photo"><MaterialIcon name="restart_alt" className="align-middle" /></button>
        </div>
      </div>
      {view === "side" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md" id="view-side-by-side">
          <div className="flex flex-col gap-space-xs bg-surface-container rounded-xl p-space-sm shadow-md border border-surface-container-high">
            <div className="flex items-center justify-between px-space-xs py-1">
              <span className="px-space-xs py-0.5 rounded bg-surface-container-highest text-on-surface-variant text-label-sm font-label-sm uppercase tracking-wider font-semibold">Original Photo</span>
              <span className="text-label-sm font-label-sm text-outline">{photo?.dimensions || "Source"}</span>
            </div>
            <div className="relative w-full aspect-square rounded-lg overflow-hidden bg-surface-container-lowest flex items-center justify-center group border border-surface-container">
              {photo ? <img id="original-preview" src={photo.url} alt="Original uploaded photo" className="w-full h-full object-contain" /> : (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-lowest/80 text-on-surface-variant p-space-md text-center">
                  <MaterialIcon name="image_not_supported" className="text-display-lg text-outline mb-space-xs" />
                  <p className="font-title-sm text-title-sm text-on-surface">No Image Loaded</p>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">Upload a photo to begin</p>
                </div>
              )}
            </div>
          </div>
          <div className="flex flex-col gap-space-xs bg-surface-container rounded-xl p-space-sm shadow-md border border-surface-container-high">
            <div className="flex items-center justify-between px-space-xs py-1">
              <div className="flex items-center gap-space-xs">
                <span className="px-space-xs py-0.5 rounded bg-primary/20 text-primary text-label-sm font-label-sm uppercase tracking-wider font-semibold">Styled Photo Result</span>
                <span className={`w-2 h-2 rounded-full ${generating ? "bg-primary animate-ping" : resultUrl ? "bg-secondary" : "bg-outline"}`} />
              </div>
              <span className="text-label-sm font-label-sm text-secondary font-semibold">{generating ? "Styling..." : resultUrl ? "WebP Ready" : "Standby"}</span>
            </div>
            <div className="relative w-full aspect-square rounded-lg overflow-hidden bg-surface-container-lowest flex items-center justify-center border border-surface-container">
              {resultUrl && <img id="styled-preview" src={resultUrl} alt="Final photo with branded mockup" className="w-full h-full object-contain" />}
              {!resultUrl && !generating && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-lowest/85 text-on-surface-variant p-space-md text-center">
                  <div className="w-14 h-14 rounded-full bg-surface-container-high flex items-center justify-center mb-space-sm text-primary shadow-[0_0_20px_rgba(245,158,11,0.2)] border border-primary/20"><MaterialIcon name="wb_sunny" className="text-headline-md" /></div>
                  <p className="font-title-sm text-title-sm text-on-surface">Ready to Celebrate</p>
                  <p className="font-body-sm text-body-sm text-on-surface-variant max-w-xs mt-1">Select a celebration style and click “Generate Celebration Photo” to see the result.</p>
                </div>
              )}
              {generating && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-lowest/90 backdrop-blur-sm z-20" role="status">
                  <div className="relative flex items-center justify-center">
                    <div className="w-20 h-20 rounded-full border-4 border-surface-container border-t-primary border-r-secondary animate-spin" />
                    <MaterialIcon name="wb_sunny" className="text-primary text-headline-sm absolute" />
                  </div>
                  <span className="font-title-md text-title-md text-on-surface mt-space-md">Creating Stylized Photo</span>
                  <span className="font-body-sm text-body-sm text-secondary">Applying selected photo style...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <BeforeAfterComparison
          photoUrl={photo!.url}
          resultUrl={resultUrl!}
          position={position}
          onPositionChange={setPosition}
        />
      )}
    </>
  );
}
