import { useCelebrationTheme } from "../../context/CelebrationThemeContext";
import { DesertHorizon } from "../effects/DesertHorizon";
import { BrandLogo } from "./BrandLogo";

export function Hero() {
  const { style } = useCelebrationTheme();
  const isPharaonic = style === "pharaonic";

  return (
    <section className="theme-hero relative overflow-hidden w-full pt-space-xl pb-space-lg px-margin flex flex-col items-center justify-center text-center">
      {isPharaonic && <DesertHorizon />}
      <div
        aria-hidden="true"
        className="theme-hero-glow absolute top-0 left-1/2 -translate-x-1/2 w-[720px] h-[360px] bg-gradient-to-b from-primary-container/25 via-secondary-container/15 to-transparent blur-3xl pointer-events-none rounded-full"
      />
      <div
        aria-hidden="true"
        className="theme-hero-glow absolute -top-10 left-1/4 w-72 h-72 bg-primary/15 blur-3xl pointer-events-none rounded-full"
      />
      <div
        aria-hidden="true"
        className="theme-hero-glow absolute -top-10 right-1/4 w-72 h-72 bg-secondary/15 blur-3xl pointer-events-none rounded-full"
      />
      <div className="flex w-full justify-center items-center leading-none mb-0 p-0">
        <BrandLogo className="block h-[10pc] w-auto" />
      </div>
      <h1 className="relative font-display-lg text-display-lg text-on-surface max-w-4xl tracking-tight leading-tight font-bold">
        {isPharaonic
          ? "Turn Your Photo into Pharaonic Art: "
          : "Celebrate with Us: "}
        <span className="theme-hero-emphasis bg-gradient-to-r from-primary via-primary-container to-secondary bg-clip-text text-transparent">
          {isPharaonic
            ? "Try Our AI Photo Tool: "
            : "Add Christmas Magic to Your Photos with AI"}
        </span>
      </h1>
      <p className="relative font-body-lg text-body-lg text-on-surface-variant max-w-2xl mt-space-md">
        {isPharaonic
          ? "Give your favourite photo a Pharaonic twist. Upload your image and use AI to try ancient Egyptian outfits, royal details and a fresh look inspired by Egypt's history."
          : "Bring Christmas to your Egypt photos! Upload your favourite travel shot and add Santa hats, falling snow, reindeer and festive scenes with our AI photo tool from Sun Pyramids Tours."}
      </p>
    </section>
  );
}
