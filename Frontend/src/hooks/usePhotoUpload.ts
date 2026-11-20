import { useCallback, useEffect, useRef, useState } from "react";
import { loadImage } from "../services/imageLoader";
import { describePhoto, validatePhotoFile } from "../services/imageValidation";
import type { SourcePhoto } from "../types/studio";

/** The uploaded image and its URL belong together in one hook. */
export function usePhotoUpload(
  invalidateResult: () => void,
  notify: (message: string, isError?: boolean) => void,
  setError: (message: string) => void,
) {
  const [photo, setPhoto] = useState<SourcePhoto | null>(null);
  const [loadingPhoto, setLoadingPhoto] = useState(false);
  const photoUrlRef = useRef<string | null>(null);
  const uploadRevision = useRef(0);

  const clearPhoto = useCallback(() => {
    uploadRevision.current += 1;
    invalidateResult();
    if (photoUrlRef.current) URL.revokeObjectURL(photoUrlRef.current);
    photoUrlRef.current = null;
    setPhoto(null);
    setLoadingPhoto(false);
    setError("");
  }, [invalidateResult, setError]);

  const selectPhoto = useCallback(async (file?: File) => {
    if (!file) return;
    // Invalid selections also supersede any older upload still decoding.
    const revision = ++uploadRevision.current;
    const validation = validatePhotoFile(file);
    if (!validation.valid) {
      setError(validation.message ?? "Invalid image.");
      notify(validation.notice ?? "Invalid image.", true);
      setLoadingPhoto(false);
      return;
    }

    setError("");
    setLoadingPhoto(true);
    const candidateUrl = URL.createObjectURL(file);

    try {
      const image = await loadImage(candidateUrl);
      if (revision !== uploadRevision.current) {
        URL.revokeObjectURL(candidateUrl);
        return;
      }
      if (!image.naturalWidth || !image.naturalHeight) {
        throw new Error("The selected file is not a valid image.");
      }

      // Just like the original, a new upload replaces the old image only
      // once decoding has succeeded (not when the file is first selected).
      invalidateResult();
      if (photoUrlRef.current) URL.revokeObjectURL(photoUrlRef.current);
      photoUrlRef.current = candidateUrl;
      setPhoto(describePhoto(file, candidateUrl, image));
      notify("Photo ready. Choose a style to generate a preview.");
    } catch (caught) {
      URL.revokeObjectURL(candidateUrl);
      if (revision === uploadRevision.current) {
        const message = caught instanceof Error ? caught.message : "Unable to read the image.";
        setError(message);
        notify(message, true);
      }
    } finally {
      if (revision === uploadRevision.current) setLoadingPhoto(false);
    }
  }, [invalidateResult, notify, setError]);

  useEffect(() => () => {
    uploadRevision.current += 1;
    if (photoUrlRef.current) URL.revokeObjectURL(photoUrlRef.current);
  }, []);

  return { photo, loadingPhoto, selectPhoto, clearPhoto };
}
