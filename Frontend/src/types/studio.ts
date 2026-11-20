/** Public generation signatures; never use the user-facing label as an API value. */
export type StyleId =
  | "christmas-1"
  | "christmas-2"
  | "pharaonic-1"
  | "pharaonic-2";

/** Theme visuals are category-based, independent of the selected generation variant. */
export type CelebrationCategory = "christmas" | "pharaonic";

/** Legacy local renderer accepts categories, not backend generation signatures. */
export type PresetId = CelebrationCategory;

export interface SourcePhoto {
  file: File;
  url: string;
  dimensions: string;
  sizeLabel: string;
}

export interface ToastMessage {
  id: number;
  message: string;
  error?: boolean;
}
