import { useCallback, useState } from "react";
import type { GeneratedImage } from "../services/imageGeneration.api";
import { prepareFacebookShare } from "../services/facebookSharing.api";
import { EXPORT_FILENAME } from "../services/photoExport";

type Notice = (message: string, isError?: boolean) => void;

/**
 * Two distinct share paths:
 * - native: hand the actual branded WebP File to an installed mobile app;
 * - Facebook: open the verified, publicly served preview through Facebook.
 * Neither path exposes the private MinIO object-storage endpoint.
 */
export function usePhotoSharing(image: GeneratedImage | null, notify: Notice) {
  const [facebookLoading, setFacebookLoading] = useState(false);

  const shareNative = useCallback(() => {
    if (!image) return;
    if (typeof navigator.share !== "function") {
      notify("Native sharing is not available in this browser. Open this page on a supported mobile device.", true);
      return;
    }

    const photoFile = new File([image.blob], EXPORT_FILENAME, { type: "image/webp" });
    const files = [photoFile];
    const supportsFiles = typeof navigator.canShare === "function"
      && navigator.canShare({ files });

    // Crucial: call navigator.share directly within the button click's user
    // activation, not after awaiting a fetch or Blob conversion.
    const shareData: ShareData | null = supportsFiles
      ? { files, title: "My Sun Pyramids celebration photo" }
      : image.storageStatus === "stored" && image.previewUrl
        ? { url: image.previewUrl, title: "My Sun Pyramids celebration photo" }
        : null;

    if (!shareData) {
      notify("This device cannot share image files, and no public photo link is available.", true);
      return;
    }

    if (!supportsFiles) {
      notify("Your device cannot share this WebP file directly, so it will share the photo link instead.");
    }
    void navigator.share(shareData).catch((error: unknown) => {
      if (error instanceof DOMException && error.name === "AbortError") return;
      notify("Could not open the native share sheet on this device.", true);
    });
  }, [image, notify]);

  const shareFacebook = useCallback(() => {
    if (!image || image.storageStatus !== "stored" || facebookLoading) return;
    setFacebookLoading(true);

    // Open the window before the async request, while the click has popup permission.
    const shareWindow = window.open("", "_blank");
    if (shareWindow) shareWindow.opener = null;

    void prepareFacebookShare(image.photoId)
      .then(result => {
        if (shareWindow && !shareWindow.closed) {
          shareWindow.location.replace(result.shareUrl);
        } else {
          window.location.assign(result.shareUrl);
        }
      })
      .catch((error: unknown) => {
        shareWindow?.close();
        notify(error instanceof Error ? error.message : "Facebook sharing is unavailable.", true);
      })
      .finally(() => setFacebookLoading(false));
  }, [image, facebookLoading, notify]);

  return {
    shareNative,
    shareFacebook,
    facebookEnabled: image?.storageStatus === "stored" && Boolean(image.previewUrl),
    facebookLoading,
  };
}
