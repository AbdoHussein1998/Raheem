import type { PhotoStudioController } from "../../hooks/usePhotoStudio";
import { MaterialIcon } from "../ui/MaterialIcon";
import { PhotoUploader } from "./PhotoUploader";
import { StyleSelector } from "./StyleSelector";

export function EditorPanel({ studio }: { studio: PhotoStudioController }) {
  return (
    <div className="theme-card lg:col-span-5 flex flex-col gap-space-md bg-surface-container rounded-xl p-space-lg shadow-xl border border-surface-container-high">
      <PhotoUploader
        photo={studio.photo}
        loading={studio.loadingPhoto}
        onSelect={file => void studio.selectPhoto(file)}
        onRemove={studio.removePhoto}
      />
      <hr className="border-0 h-[1px] bg-surface-variant/40" />
      <StyleSelector
        style={studio.style}
        onStyleChange={studio.changeStyle}
      />
      <hr className="border-0 h-[1px] bg-surface-variant/40" />
      <div className="flex flex-col gap-space-xs">
        <button
          type="button"
          disabled={studio.generating || studio.loadingPhoto}
          onClick={() => void studio.generate()}
          className="theme-main-action w-full py-space-sm px-space-md rounded-lg font-title-md text-title-md flex items-center justify-center gap-space-sm bg-gradient-to-r from-primary via-primary-container to-secondary text-on-primary-container shadow-[0_0_20px_rgba(245,158,11,0.35)] hover:shadow-[0_0_28px_rgba(76,215,246,0.45)] transition-all transform hover:-translate-y-0.5 active:translate-y-0 font-bold disabled:opacity-60 disabled:cursor-wait"
        >
          <MaterialIcon name={studio.generating ? "hourglass_top" : studio.resultUrl ? "refresh" : "auto_awesome"} className={`text-headline-sm ${studio.generating ? "animate-spin" : ""}`} />
          {studio.generating ? "Styling Photo..." : studio.resultUrl ? "Generate Again" : "Generate Celebration Photo"}
        </button>
        {studio.progressStatus !== "idle" && (
          <div className="flex flex-col gap-1 mt-space-xs">
            <div className="flex items-center justify-between gap-2 text-label-sm font-label-sm">
              <span className="flex items-center gap-1 text-primary">
                <MaterialIcon
                  name={studio.progressStatus === "complete" ? "check_circle" : "refresh"}
                  className={`text-label-sm ${studio.progressStatus === "running" ? "animate-spin" : ""}`}
                />
                {studio.progressStatus === "complete"
                  ? "Photo generated successfully"
                  : studio.progress >= 90
                    ? "Waiting for generated photo..."
                    : "Rendering selected photo style..."}
              </span>
              <span className="text-secondary font-semibold tabular-nums">
                {studio.progress}%
              </span>
            </div>
            <div
              className="w-full h-1.5 rounded-full bg-surface-container-lowest overflow-hidden"
              role="progressbar"
              aria-label="Photo generation progress"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={studio.progress}
            >
              <div
                className="h-full bg-gradient-to-r from-primary to-secondary transition-[width] duration-200 ease-linear"
                style={{ width: `${studio.progress}%` }}
              />
            </div>
          </div>
        )}
        {studio.error && (
          <div className="p-space-xs rounded bg-error-container text-on-error-container text-label-sm font-label-sm flex items-start gap-1" role="alert">
            <MaterialIcon name="error" className="text-label-sm" />
            <span>{studio.error}</span>
          </div>
        )}
      </div>
    </div>
  );
}
