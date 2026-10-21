# Raheem Frontend

Arabic RTL React / TypeScript website built with Vite, React Router and Tailwind CSS v4.

## Setup

```bash
npm ci
npm run dev
```

Production build: `npm run build`  ·  Lint: `npm run lint`.

## Directory structure

```text
src/
├── features/
│   ├── home/components/Hero.tsx
│   └── gateways/
│       ├── components/{GatewayCard,GatewayGrid}.tsx
│       ├── config/gateways.ts
│       └── types/gateway.ts
├── components/layout/
│   ├── Header.tsx
│   ├── Footer.tsx
│   ├── MobileNavigation.tsx
│   ├── ThemeToggle.tsx
│   └── MainLayout.tsx
├── hooks/useTheme.ts
├── pages/{HomePage,GatewayPage,NotFoundPage}.tsx
├── services/apiClient.ts
├── config/env.ts
├── routes/AppRoutes.tsx
├── assets/raheem-logo.ico
├── styles/global.css
├── App.tsx
└── main.tsx
```

### Boundaries

- `components/layout`: shared header, footer, navigation, and the `<Outlet />` that renders pages.
- `pages`: route-level composition. Do not put the shared header/footer inside each page.
- `features/*`: components/data/types unique to that feature. Keep gateway data and styling class strings together.
- `hooks`: reusable stateful UI logic. `useTheme` stores the user's light/dark preference.
- `services`: generic network code. Add feature-specific API services once real endpoint contracts exist.
- `styles/global.css`: original Tailwind design tokens and theme definitions; preserve class names when changing JSX.

### Routes

| URL | Result |
| --- | --- |
| `/` | Homepage |
| `/news`, `/ask-raheem`, `/consultations`, `/endowment` | Existing gateway information, labelled as under development |
| Other paths | Not-found page |

The uploaded project does **not** implement image processing or authentication, and it contains no endpoint-specific backend integration. Therefore neither feature is fabricated in this refactor. Add each when needed as `src/features/<name>/{components,hooks,services,types}`. The `VITE_API_BASE_URL` environment variable configures the existing generic API client (default: `http://localhost:8000`).

### Architecture notes

- `src/main.tsx` is the only React mounting entry point.
- `src/App.tsx` owns the root route tree through `AppRoutes`.
- `MainLayout` persists across child-page navigation and renders `<Outlet />`.
- The original appearance, Arabic copy, gateway class strings, footer, theme toggle and responsive navigation are preserved.
- Existing gateway cards advertise destinations without working features in the source. Those destinations now show transparent informational placeholders instead of blank screens.
