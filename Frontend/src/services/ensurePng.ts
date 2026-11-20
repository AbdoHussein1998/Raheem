import { loadImage } from "./imageLoader";

/** The UI promises a PNG export even when the backend returns JPEG/WebP. */
export async function ensurePng(blob: Blob): Promise<Blob> {
  if (blob.type === "image/png") return blob;

  const temporaryUrl = URL.createObjectURL(blob);
  try {
    const image = await loadImage(temporaryUrl);
    const canvas = document.createElement("canvas");
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Your browser does not support PNG export.");
    context.drawImage(image, 0, 0);

    return await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        result => result ? resolve(result) : reject(new Error("Could not encode PNG.")),
        "image/png",
      );
    });
  } finally {
    URL.revokeObjectURL(temporaryUrl);
  }
}
