import type { StyleId } from "../types/studio";

/** Input required for the NestJS image-generation endpoint. */
interface GenerateImageRequest {
  apiUrl: string;
  file: File;
  style: StyleId;
  signal: AbortSignal;
}

interface GenerateImageResponse {
  success: boolean;
  message?: string;
  data?: {
    fileName: string;
    mimeType: string;
    originalSize: number;
    compressedSize: number;
    downloadFileName: string;
    imageSize: number;
    width: number;
    height: number;
    imageDataUrl: string;
    photoId: string;
    previewUrl: string | null;
    storageStatus: "stored" | "unavailable";
  };
}

/** Branded WebP and the independent storage metadata required by Facebook. */
export interface GeneratedImage {
  blob: Blob;
  photoId: string;
  previewUrl: string | null;
  storageStatus: "stored" | "unavailable";
}

export class ImageApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ImageApiError";
  }
}

/**
 * Only HTTP transport and decoding belong here: no React state, no mockup
 * calculations, and no construction of direct private MinIO URLs.
 */
export async function requestGeneratedImage({
  apiUrl, file, style, signal,
}: GenerateImageRequest): Promise<GeneratedImage> {
  const body = new FormData();
  body.append("image", file, file.name);
  // Stable signature (e.g. "pharaonic-2"), never the display label.
  body.append("prompt", style);

  const response = await fetch(apiUrl, {
    method: "POST",
    body,
    credentials: "include",
    signal,
  });

  const result: GenerateImageResponse | null = await response.json().catch(() => null);
  if (!response.ok) {
    const message = typeof result?.message === "string"
      ? result.message
      : `Image processing failed (HTTP ${response.status}).`;
    throw new ImageApiError(response.status, message);
  }

  const data = result?.data;
  if (result?.success !== true || !data || typeof data.imageDataUrl !== "string"
    || typeof data.photoId !== "string"
    || (data.storageStatus !== "stored" && data.storageStatus !== "unavailable")
    || (data.previewUrl !== null && typeof data.previewUrl !== "string")
    || (data.storageStatus === "stored" && !data.previewUrl)) {
    throw new Error("The server did not return a valid generated image.");
  }

  const match = /^data:image\/webp;base64,([A-Za-z0-9+/]+={0,2})$/i.exec(data.imageDataUrl);
  if (!match || data.mimeType !== "image/webp") {
    throw new Error("The server returned an unsupported image format.");
  }

  try {
    const binary = atob(match[1]);
    const bytes = Uint8Array.from(binary, character => character.charCodeAt(0));
    return {
      blob: new Blob([bytes], { type: "image/webp" }),
      photoId: data.photoId,
      previewUrl: data.previewUrl,
      storageStatus: data.storageStatus,
    };
  } catch {
    throw new Error("The generated image could not be decoded.");
  }
}
