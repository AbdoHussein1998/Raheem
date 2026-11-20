import styleOptions from "../config/style-options.json";
import type { CelebrationCategory, PresetId, StyleId } from "../types/studio";

export type StyleThemeCategory = CelebrationCategory;

export interface StyleCategoryOption {
  id: StyleThemeCategory;
  name: string;
  icon: string;
  detail: string;
}

export const STYLE_CATEGORIES: readonly StyleCategoryOption[] = [
  {
    id: "christmas",
    name: "Christmas",
    icon: "park",
    detail: "Festive warmth and seasonal highlights",
  },
  {
    id: "pharaonic",
    name: "Pharaonic",
    icon: "history_edu",
    detail: "Warm desert luminance & crisp highlights",
  },
];

/**
 * A label is presentation-only; a value is the stable backend prompt signature.
 * To rename a style shown to visitors, only edit src/config/style-options.json.
 */
export interface StyleOption {
  value: StyleId;
  label: string;
  detail: string;
  category: StyleThemeCategory;
}

// TypeScript gives imported JSON string properties a broad `string` type.
// The list remains the source of truth for selectable values; the API separately
// rejects every signature outside its explicit allowlist.
export const STYLE_OPTIONS: readonly StyleOption[] = STYLE_CATEGORIES.flatMap(category =>
  styleOptions[category.id].map(option => ({
    value: option.value as StyleId,
    label: option.label,
    detail: option.detail,
    category: category.id,
  })),
);

export function getStylesForCategory(category: StyleThemeCategory): readonly StyleOption[] {
  return STYLE_OPTIONS.filter(option => option.category === category);
}

export function getCategoryForStyle(styleId: StyleId): StyleThemeCategory {
  const match = STYLE_OPTIONS.find(option => option.value === styleId);
  if (!match) throw new Error(`Unknown style: ${styleId}`);
  return match.category;
}

export function isStyleId(value: string): value is StyleId {
  return STYLE_OPTIONS.some(option => option.value === value);
}

/** Legacy canvas-only presets. The active backend path never uses these. */
interface LocalStylePreset {
  filter: string;
  primary: [number, number, number];
  secondary: [number, number, number];
}

export const STYLE_PRESETS: Record<PresetId, LocalStylePreset> = {
  christmas: {
    filter: "brightness(1.05) saturate(1.17) contrast(1.04)",
    primary: [246, 190, 101],
    secondary: [196, 71, 87],
  },
  pharaonic: {
    filter: "sepia(0.16) saturate(1.14) brightness(1.05) contrast(1.07)",
    primary: [235, 180, 94],
    secondary: [208, 144, 72],
  },
};
