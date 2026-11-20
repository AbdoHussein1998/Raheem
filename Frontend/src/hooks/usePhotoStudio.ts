import { useCallback, useState } from "react";
import { useToastNotification } from "./useToastNotification";
import { useImageGeneration } from "./useImageGeneration";
import { usePhotoUpload } from "./usePhotoUpload";
import { useStudioStyles } from "./useStudioStyles";

/** Coordinates the upload, style, generation, and notification hooks. */
export function usePhotoStudio() {
  const [error, setError] = useState("");
  const { toast, notify } = useToastNotification();
  const { resultUrl, generatedImage, generating, progress, progressStatus, invalidateResult, generate: createImage } =
    useImageGeneration(notify, setError);
  const { photo, loadingPhoto, selectPhoto, clearPhoto } =
    usePhotoUpload(invalidateResult, notify, setError);
  const clearError = useCallback(() => setError(""), []);
  const removePhoto = useCallback(() => {
    clearPhoto();
    notify("Photo removed.");
  }, [clearPhoto, notify]);
  const { style, changeStyle } = useStudioStyles(invalidateResult, clearError);

  const generate = useCallback(() => createImage({ photo, style }), [createImage, photo, style]);

  return {
    photo, resultUrl, generatedImage, style,
    loadingPhoto, generating, progress, progressStatus, error, toast,
    setError, notify, selectPhoto, clearPhoto, removePhoto,
    changeStyle, generate,
  };
}

export type PhotoStudioController = ReturnType<typeof usePhotoStudio>;
