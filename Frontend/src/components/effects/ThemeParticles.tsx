import type { CSSProperties } from "react";
import type { CelebrationCategory } from "../../types/studio";

interface Particle {
  id: number;
  left: number;
  top: number;
  size: number;
  duration: number;
  delay: number;
  drift: number;
  opacity: number;
}

/** Seeded, module-level data: stable particles across re-renders and no animation libraries. */
function createParticles(count: number, seed: number, style: CelebrationCategory): Particle[] {
  let value = seed;
  const random = () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return value / 4294967296;
  };

  return Array.from({ length: count }, (_, id) => {
    const duration = style === "christmas" ? 9 + random() * 14 : 7 + random() * 12;
    return {
      id,
      left: random() * 100,
      top: style === "christmas" ? -12 : 12 + random() * 82,
      size: style === "christmas" ? 2 + random() * 5 : 1 + random() * 3.5,
      duration,
      delay: -random() * duration,
      drift: (random() - 0.5) * (style === "christmas" ? 190 : 110),
      opacity: style === "christmas" ? 0.3 + random() * 0.6 : 0.25 + random() * 0.5,
    };
  });
}

const SNOW = createParticles(75, 2026, "christmas");
const SAND = createParticles(55, 1799, "pharaonic");

type ParticleProperties = CSSProperties & {
  "--particle-drift": string;
  "--particle-opacity": number;
};

/** Purely decorative fixed overlay. Never captures pointer or keyboard input. */
export function ThemeParticles({ style }: { style: CelebrationCategory }) {
  const particles = style === "christmas" ? SNOW : SAND;

  return (
    <div className={`theme-atmosphere theme-atmosphere--${style}`} aria-hidden="true">
      {particles.map(particle => {
        const properties: ParticleProperties = {
          left: `${particle.left}%`,
          top: `${particle.top}%`,
          width: `${particle.size}px`,
          height: `${particle.size}px`,
          animationDuration: `${particle.duration}s`,
          animationDelay: `${particle.delay}s`,
          "--particle-drift": `${particle.drift}px`,
          "--particle-opacity": particle.opacity,
        };

        return <span key={particle.id} className="theme-particle" style={properties} />;
      })}
    </div>
  );
}
