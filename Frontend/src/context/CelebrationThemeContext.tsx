import { createContext, useContext, useMemo, useState } from "react";
import type { PropsWithChildren } from "react";
import type { CelebrationCategory } from "../types/studio";

interface CelebrationThemeValue {
  style: CelebrationCategory;
  setStyle: (style: CelebrationCategory) => void;
}

const CelebrationThemeContext = createContext<CelebrationThemeValue | null>(null);

/** The page-wide appearance is shared; photo generation remains in its own hooks. */
export function CelebrationThemeProvider({ children }: PropsWithChildren) {
  const [style, setStyle] = useState<CelebrationCategory>("christmas");
  const value = useMemo(() => ({ style, setStyle }), [style]);

  return (
    <CelebrationThemeContext.Provider value={value}>
      {children}
    </CelebrationThemeContext.Provider>
  );
}

export function useCelebrationTheme(): CelebrationThemeValue {
  const context = useContext(CelebrationThemeContext);
  if (!context) {
    throw new Error("useCelebrationTheme requires CelebrationThemeProvider.");
  }
  return context;
}
