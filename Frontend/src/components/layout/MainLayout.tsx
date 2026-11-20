import { Outlet } from "react-router-dom";
import {
  CelebrationThemeProvider,
  useCelebrationTheme,
} from "../../context/CelebrationThemeContext";
import { ThemeParticles } from "../effects/ThemeParticles";
import { FestiveGarlands } from "./FestiveGarlands";
import { Header } from "./Header";
import { Footer } from "./Footer";

/** Shared shell reacts to the same style chosen by the photo studio. */
function CelebrationLayout() {
  const { style } = useCelebrationTheme();

  return (
    <div
      className="celebration-shell bg-background font-body-md text-body-md text-on-surface antialiased min-h-screen flex flex-col"
      data-celebration-theme={style}
    >
      <ThemeParticles style={style} />
      {style === "christmas" && <FestiveGarlands />}
      <Header />
      <Outlet />
      <Footer />
    </div>
  );
}

export default function MainLayout() {
  return (
    <CelebrationThemeProvider>
      <CelebrationLayout />
    </CelebrationThemeProvider>
  );
}
