# Widget Warehouse Client Guide

This directory contains the Widget Warehouse Vue 3 client. It is a Vite app
that consumes the VUEDA client package. VUEDA questions are answered from
<https://vueda.dev/v3/>; see the root guide's VUEDA Documentation section.

## Commands

Run these from the repo root unless a command explicitly says otherwise:

- Install dependencies: `just bootstrap`
- Check client: `just check-client`
- Fix client: `just fix-client`
- Test client: `just test-client`
- Build app client: `just build`
- Preview production app with local server: `just preview`
- Serve client only: `just serve-client`
- Build client only: `just build-client`
- Preview production client only: `just preview-client`

Package scripts in `client/package.json`:

- `pnpm run dev`: Vite dev server
- `pnpm run build`: Vite production build
- `pnpm test run`: Vitest
- `pnpm run lint`: ESLint check
- `pnpm run format`: Prettier check
- `pnpm run eslint`: ESLint fix
- `pnpm run prettier`: Prettier write

## Architecture

- Entry point: `src/main.js`
- App shell: `src/TheApp.vue`
- Navigation: `src/TheNav.vue` and `src/nav/`
- Router: `src/router/index.js`
- View components: `src/views/`

The router uses VUEDA CRUD helpers. `makeViewLoader()` first looks for a
model-specific component named `View<Action><App><Model>.vue`, then falls back
to `DefaultView<Action>.vue`.

## Code Style

- Plain JavaScript and Vue SFCs. There are no TypeScript files in the client.
- Use the existing alias patterns: `@/` for local client source and `@vueda/`
  for linked VUEDA client source.
- Keep imports compatible with the configured Prettier import sorting.
- Prettier uses 4 spaces, trailing commas, and a 120 character print width.
- ESLint combines neostandard, Vue recommended rules, and Prettier.

## UI Guidance

- Reuse VUEDA components and app patterns before adding local abstractions.
- Keep CRUD view behavior aligned with server metadata and VUEDA routing.
- Prefer model-specific views only when the default VUEDA-backed CRUD views are
  not enough.

## Testing

- Use Vitest for client tests.
- Prefer focused tests around routing, view selection, and client behavior when
  changing shared UI or CRUD integration.
- If a change depends on the linked VUEDA package, state that dependency in the
  verification notes.
