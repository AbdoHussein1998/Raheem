import { Hero } from "../components/layout/Hero";
import { UnauthorizedMessage } from "../components/layout/UnauthorizedMessage";

export function Unauthorized() {
  return (
    <main className="w-full pt-20 sm:pt-24 bg-background min-h-screen flex flex-col flex-1">
      <Hero />
      <UnauthorizedMessage />
    </main>
  );
}
