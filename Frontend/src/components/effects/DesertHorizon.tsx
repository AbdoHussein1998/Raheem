/** Visual-only hero illustration. The generated photo and its export are unaffected. */
export function DesertHorizon() {
  return (
    <div className="hero-desert-art" aria-hidden="true">
      <div className="hero-desert-sun" />
      <svg
        viewBox="0 0 1440 360"
        preserveAspectRatio="xMidYMax slice"
        focusable="false"
      >
        <defs>
          <linearGradient id="desert-pyramid-face" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0" stopColor="#c09255" stopOpacity=".7" />
            <stop offset="1" stopColor="#5e3b22" stopOpacity=".8" />
          </linearGradient>
        </defs>
        <path
          d="M0 260Q240 205 470 275T980 260T1440 258V360H0Z"
          fill="#b08042"
          opacity=".18"
        />
        <path
          d="M730 265 880 30 1030 265Z"
          fill="url(#desert-pyramid-face)"
          opacity=".62"
        />
        <path d="M880 30 1030 265H880Z" fill="#3d291c" opacity=".43" />
        <path d="M960 278 1096 86 1228 278Z" fill="#a16d39" opacity=".45" />
        <path d="M1096 86 1228 278H1096Z" fill="#3a281d" opacity=".37" />
        <path d="M570 280 665 146 760 280Z" fill="#c09358" opacity=".32" />
        <path
          d="M0 293Q185 247 410 300T850 301T1440 280V360H0Z"
          fill="#a77239"
          opacity=".27"
        />
        <path
          d="M0 321Q260 273 540 322T1100 305T1440 320V360H0Z"
          fill="#d49a4b"
          opacity=".16"
        />
      </svg>
    </div>
  );
}
