import {
  isStyleId,
  STYLE_CATEGORIES,
  STYLE_OPTIONS,
  getCategoryForStyle,
  getStylesForCategory,
  type StyleThemeCategory,
} from "../../constants/styles";
import type { StyleId } from "../../types/studio";
import { MaterialIcon } from "../ui/MaterialIcon";
import { ChristmasTreeIcon, PharaonicMaskIcon } from "../ui/CelebrationIcons";

interface Props {
  style: StyleId;
  onStyleChange: (value: StyleId) => void;
}

/**
 * Presents style selection via two theme category buttons (Christmas and Pharaonic)
 * with a dropdown below to choose specific style variants for the active theme.
 */
export function StyleSelector({ style, onStyleChange }: Props) {
  const activeCategory: StyleThemeCategory = getCategoryForStyle(style);
  const availableStyles = getStylesForCategory(activeCategory);
  const active =
    availableStyles.find(option => option.value === style) ??
    STYLE_OPTIONS.find(option => option.value === style) ??
    availableStyles[0] ??
    STYLE_OPTIONS[0];

  const handleCategorySelect = (category: StyleThemeCategory) => {
    if (category === activeCategory) return;
    const defaultForCategory = getStylesForCategory(category)[0];
    if (defaultForCategory) {
      onStyleChange(defaultForCategory.value);
    }
  };

  const handleStyleChange = (value: string) => {
    if (isStyleId(value)) onStyleChange(value);
  };

  return (
    <div className="flex flex-col gap-space-sm">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <span className="flex items-center gap-space-xs text-title-sm font-title-sm text-on-surface">
          <span className="w-5 h-5 rounded-full bg-secondary/20 text-secondary flex items-center justify-center text-label-sm font-label-sm font-bold">
            2
          </span>
          Select Celebration Style
        </span>
        <span className="text-label-sm font-label-sm text-secondary font-semibold">
          {active?.label ?? "Select a style"}
        </span>
      </div>

      {/* Two Theme / Style Category Buttons */}
      <div className="grid grid-cols-2 gap-space-xs" role="group" aria-label="Celebration style buttons">
        {STYLE_CATEGORIES.map(category => {
          const isSelected = activeCategory === category.id;
          const isChristmas = category.id === "christmas";
          return (
            <button
              key={category.id}
              type="button"
              onClick={() => handleCategorySelect(category.id)}
              className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-title-sm font-title-sm transition-all border cursor-pointer ${
                isSelected
                  ? "bg-surface-container-high text-primary border-primary shadow-[0_0_12px_rgba(245,158,11,0.25)] font-bold"
                  : "bg-surface-container-lowest text-on-surface-variant border-surface-container-high hover:text-on-surface hover:bg-surface-container-high/60"
              }`}
              aria-pressed={isSelected}
            >
              {isChristmas ? (
                <ChristmasTreeIcon
                  className={`w-5 h-5 shrink-0 ${isSelected ? "text-primary" : "text-on-surface-variant"}`}
                />
              ) : (
                <PharaonicMaskIcon
                  className={`w-5 h-5 shrink-0 ${isSelected ? "text-primary" : "text-on-surface-variant"}`}
                />
              )}
              <span>{category.name}</span>
            </button>
          );
        })}
      </div>

      {/* Style Dropdown under the two buttons */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between text-label-sm font-label-sm text-on-surface-variant">
          <label htmlFor="style-selector">Style Variant</label>
          <span className="text-secondary font-medium truncate max-w-[200px]" title={active?.detail}>
            {active?.detail}
          </span>
        </div>
        <div className="relative">
          <select
            id="style-selector"
            value={active?.value ?? ""}
            onChange={event => handleStyleChange(event.target.value)}
            className="theme-select w-full appearance-none rounded-lg bg-surface-container-lowest px-space-md py-space-sm text-on-surface font-title-sm text-title-sm cursor-pointer focus:outline-none focus:bg-surface-container-high pr-10 border border-surface-container-high"
          >
            {availableStyles.length === 0 && <option value="">No styles available</option>}
            {availableStyles.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          <MaterialIcon
            name="expand_more"
            className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant"
          />
        </div>
      </div>
    </div>
  );
}
