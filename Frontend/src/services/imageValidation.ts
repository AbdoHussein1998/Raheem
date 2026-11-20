import type { SourcePhoto } from "../types/studio";

export const MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024;
export const ACCEPTED_IMAGE_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"] as const;

export interface ImageValidationResult {
  valid: boolean;
  message?: string;
  notice?: string;
}

export function validatePhotoFile(file: File): ImageValidationResult {
  if (!(ACCEPTED_IMAGE_MIME_TYPES as readonly string[]).includes(file.type)) {
    return { valid: false, message: "Unsupported image format. Use JPG, PNG, or WebP.", notice: "Unsupported image format." };
  }
  if (file.size > MAX_IMAGE_SIZE_BYTES) {
    return { valid: false, message: "This file exceeds the 10 MB limit.", notice: "Image must be smaller than 10 MB." };
  }
  return { valid: true };
}

export function describePhoto(file: File, url: string, image: HTMLImageElement): SourcePhoto {
  return {
    file,
    url,
    dimensions: `${image.naturalWidth} × ${image.naturalHeight}`,
    sizeLabel: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
  };
}
