import { STYLE_PRESETS } from "../constants/styles";
import type { PresetId } from "../types/studio";
import { loadImage } from "./imageLoader";

/** Browser-only preview renderer (not an AI generation engine). */
function rgba([r, g, b]: [number, number, number], alpha: number): string {
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export async function renderLocalStyle(sourceUrl: string, style: PresetId, intensity: number): Promise<Blob> {
  const image = await loadImage(sourceUrl);
  const scale = Math.min(1, 4096 / Math.max(image.naturalWidth, image.naturalHeight));
  const width = Math.max(1, Math.round(image.naturalWidth * scale));
  const height = Math.max(1, Math.round(image.naturalHeight * scale));
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Your browser does not support canvas processing.");

  const amount = Math.max(0, Math.min(1, intensity / 100));
  const preset = STYLE_PRESETS[style];
  ctx.filter = amount === 0 ? "none" : preset.filter;
  ctx.drawImage(image, 0, 0, width, height);
  ctx.filter = "none";

  if (amount > 0) {
    const glow = ctx.createRadialGradient(width * 0.76, height * 0.12, width * 0.05,
      width * 0.76, height * 0.12, Math.max(width, height) * 0.9);
    glow.addColorStop(0, rgba(preset.primary, 0.42 * amount));
    glow.addColorStop(0.5, rgba(preset.secondary, 0.17 * amount));
    glow.addColorStop(1, rgba(preset.secondary, 0));
    ctx.globalCompositeOperation = "screen";
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, width, height);

    const vignette = ctx.createRadialGradient(width / 2, height / 2, Math.min(width, height) * 0.3,
      width / 2, height / 2, Math.max(width, height) * 0.76);
    vignette.addColorStop(0, "rgba(0,0,0,0)");
    vignette.addColorStop(1, `rgba(11,19,38,${0.27 * amount})`);
    ctx.globalCompositeOperation = "multiply";
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, width, height);
    ctx.globalCompositeOperation = "source-over";
  }

  return new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error("Could not encode PNG.")), "image/png");
  });
}

