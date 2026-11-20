/** Calls NestJS for its validated, public Facebook share URL; never accesses MinIO. */
export interface FacebookShareResult {
  success: true;
  photoId: string;
  previewUrl: string;
  shareUrl: string;
}

function getShareEndpoint(photoId: string): string {
  // Derive the API's origin and prefix from the existing image endpoint;
  // no additional environment variable is required for deployment.
  const configured = import.meta.env.VITE_IMAGE_API_URL?.trim() || "/api/process/upload";
  const uploadUrl = new URL(configured, window.location.href);
  const uploadPath = "/process/upload";
  if (!uploadUrl.pathname.endsWith(uploadPath)) {
    throw new Error("VITE_IMAGE_API_URL must end in /process/upload.");
  }
  const prefix = uploadUrl.pathname.slice(0, -uploadPath.length);
  return `${uploadUrl.origin}${prefix}/sharing/facebook/profile/${encodeURIComponent(photoId)}`;
}

export async function prepareFacebookShare(photoId: string): Promise<FacebookShareResult> {
  const response = await fetch(getShareEndpoint(photoId), {
    method: "GET",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  const result: Partial<FacebookShareResult> & { message?: string } | null =
    await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(typeof result?.message === "string"
      ? result.message
      : "Facebook sharing is unavailable. Please try again.");
  }
  if (result?.success !== true || result.photoId !== photoId
    || typeof result.previewUrl !== "string"
    || typeof result.shareUrl !== "string") {
    throw new Error("The server returned an invalid Facebook sharing link.");
  }

  // Refuse an unexpected external redirect returned by a compromised API.
  const shareUrl = new URL(result.shareUrl);
  if (shareUrl.protocol !== "https:" || shareUrl.hostname !== "www.facebook.com"
      || shareUrl.pathname !== "/sharer/sharer.php") {
    throw new Error("The server returned an unsupported Facebook sharing destination.");
  }
  return result as FacebookShareResult;
}
