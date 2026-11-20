import { useCelebrationTheme } from "../../context/CelebrationThemeContext";
import { usePhotoStudio } from "../../hooks/usePhotoStudio";
import { usePhotoSharing } from "../../hooks/usePhotoSharing";
import { SharePanel } from "./SharePanel";
import { PhotoPreview } from "./PhotoPreview";
import { EditorPanel } from "./EditorPanel";
import { Toast } from "../ui/Toast";

export function PhotoStudio() {
  const { style } = useCelebrationTheme();
  const studio = usePhotoStudio();
  const { shareNative, shareFacebook, facebookEnabled, facebookLoading } =
    usePhotoSharing(studio.generatedImage, studio.notify);

  return (
    <section className="w-full px-margin pb-space-xl scroll-mt-20" id="campaign-studio">
      <div className="w-full max-w-7xl mx-auto flex flex-col gap-space-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-sm pb-space-xs">
          <div className="flex items-center gap-space-sm">
            <span className="w-3 h-3 rounded-full bg-secondary animate-ping" />
            <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">{style === "pharaonic" ? "Sun Pyramids Ancient Egypt Studio" : "Sun Pyramids Celebration Canvas"}</h2>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg items-start">
          <EditorPanel studio={studio} />
          <div className="lg:col-span-7 flex flex-col gap-space-md">
            <PhotoPreview photo={studio.photo} resultUrl={studio.resultUrl} generating={studio.generating} onReset={studio.removePhoto} onNotice={studio.notify} />
            <SharePanel
              enabled={Boolean(studio.resultUrl) && !studio.generating}
              facebookEnabled={facebookEnabled && !studio.generating}
              facebookLoading={facebookLoading}
              onNativeShare={shareNative}
              onFacebookShare={shareFacebook}
            />
          </div>
        </div>
      </div>
      <Toast toast={studio.toast} />
    </section>
  );
}
