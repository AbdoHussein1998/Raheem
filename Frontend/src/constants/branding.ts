/** Branding resources in one place; the fallback does not require external assets. */

export const BRAND_LOGO_URL = "/assets/Artboard 1.png";

const fallbackSvg =
    '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="48" viewBox="0 0 120 48"><rect width="120" height="48" rx="7" fill="#1b2633"/><path d="M16 35L32 11L48 35Z M36 35L56 17L72 35Z" fill="#eab668"/><text x="80" y="30" font-size="15" font-family="Arial" font-weight="bold" fill="#f5d18b">SP</text></svg>';

export const BRAND_FALLBACK_URL =
    `data:image/svg+xml,${encodeURIComponent(fallbackSvg)}`;