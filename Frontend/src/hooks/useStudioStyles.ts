import { useCallback, useState } from "react";
import { getCategoryForStyle } from "../constants/styles";
import { useCelebrationTheme } from "../context/CelebrationThemeContext";
import type { StyleId } from "../types/studio";

/**
 * Generation variant belongs to the studio; the global theme tracks only its
 * Christmas/Pharaonic category. Selecting any variant invalidates old results.
 */
export function useStudioStyles(
  invalidateResult: () => void,
  clearError: () => void,
) {
  const [style, setSelectedStyle] = useState<StyleId>("christmas-1");
  const { setStyle: setThemeCategory } = useCelebrationTheme();

  const changeStyle = useCallback((value: StyleId) => {
    if (value === style) return;
    setSelectedStyle(value);
    setThemeCategory(getCategoryForStyle(value));
    clearError();
    invalidateResult();
  }, [style, setThemeCategory, clearError, invalidateResult]);

  return { style, changeStyle };
}
