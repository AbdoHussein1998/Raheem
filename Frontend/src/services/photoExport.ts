export const EXPORT_FILENAME = "sun-pyramids-celebration.webp";

/** Browser download side effect stays out of presentational components. */
export function downloadPhoto(url: string, filename = EXPORT_FILENAME): void {
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
}
