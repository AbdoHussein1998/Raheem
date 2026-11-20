import { Hero } from "../components/layout/Hero";
import { PhotoStudio } from "../components/studio/PhotoStudio";

/** The only route-level page; preserves the original Hero → Studio order. */
export function HomePage() {
  return (
    <main className="w-full pt-20 sm:pt-24 bg-background min-h-screen">
      <Hero />
      <PhotoStudio />
    </main>
  );
}
