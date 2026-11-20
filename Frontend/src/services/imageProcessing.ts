import type { StyleId } from "../types/studio";
import { requestGeneratedImage, type GeneratedImage } from "./imageGeneration.api";

export interface GenerateImageOptions {
  file: File;
  style: StyleId;
  signal: AbortSignal;
}

/**
 * NestJS owns AI generation, the 845 x 935 mockup, and optional share storage.
 * The frontend must not resize or recompose the returned branded image.
 */
export async function generateImage({ file, style, signal }: GenerateImageOptions): Promise<GeneratedImage> {
  const apiUrl = import.meta.env.VITE_IMAGE_API_URL?.trim() || "/api/process/upload";
  const image = await requestGeneratedImage({ apiUrl, file, style, signal });
  if (signal.aborted) throw new DOMException("Generation was cancelled.", "AbortError");
  return image;
}
