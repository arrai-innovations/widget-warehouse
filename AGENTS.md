# Widget Warehouse Agent Guide

This is a small monorepo. Start here, then read the package guide for the area
you are working in:

- Server guide: `server/AGENTS.md`
- Client guide: `client/AGENTS.md`

## Project Purpose

Widget Warehouse is intended to be a working example of VUEDA. Treat it as both
an example application and a customization showcase:

- Exercise VUEDA features across realistic catalog, inventory, supplier, user,
  file, range, relation, and CRUD workflows.
- Demonstrate how a consuming project can customize VUEDA behavior, routes,
  model-specific views, styling, serializers, filtersets, and server metadata.
- Prefer examples that are useful to VUEDA integrators over narrowly bespoke
  app behavior.
- When adding features, consider whether the change should showcase a VUEDA
  capability, document an integration pattern, or stress-test framework
  behavior.

## Package Managers

This repo uses two workspace managers, both rooted here:

- **Python**: uv workspace (`pyproject.toml`). Member: `server/`.
  `just bootstrap` runs `uv sync --all-groups --all-packages`.
  Use `uv run --no-sync` inside `server/` after bootstrap.
- **JS**: pnpm workspace (`pnpm-workspace.yaml`). Member: `client/`.
  `just bootstrap` runs `pnpm install` from the root. Lefthook,
  commitlint, and shared JS tooling live in the root package.

## Common Commands

- Bootstrap: `just bootstrap`
- Checks: `just check`
- Fix formatting and lint issues: `just fix`
- Tests: `just test`
- Build app client: `just build`
- Preview production app with local server: `just preview`
- Run local app: `just serve`
- Django management commands: `just manage <command>`

Package-specific commands:

| Recipe | Runs |
|--------|------|
| `just check-server` | Ruff check and Ruff format check in `server/` |
| `just check-client` | ESLint and Prettier checks in `client/` |
| `just fix-server` | Ruff fixes and formatting in `server/` |
| `just fix-client` | ESLint fixes and Prettier formatting in `client/` |
| `just test-server` | Pytest in `server/` |
| `just test-client` | Vitest in `client/` |
| `just build-client` | Vite production build in `client/` |
| `just preview-client` | Vite production build preview in `client/` |
| `just serve-server` | Gunicorn with Uvicorn worker on port 8000 |
| `just serve-client` | Vite dev server |

`test-server` and `test-client` accept extra arguments, which are forwarded to
the underlying test runner (pytest or vitest). Paths must be relative to the
package directory, not the repo root.

```bash
just test-server tests/test_widget_filters.py
just test-server -k below_reorder
just test-client src/setupModelConfig.spec.js
```

## VUEDA Documentation

Answer VUEDA questions from the published docs at <https://vueda.dev/v3/>, not
from guesswork and not by assuming a VUEDA checkout sits next to this one. A
sibling checkout is one contributor's local arrangement, so nothing committed
here should depend on it or cite a path inside it.

Useful entry points:

- Architecture overview:
  <https://vueda.dev/v3/core-concepts/architecture-overview.html>
- Registering a model so the metadata API and client can see it:
  <https://vueda.dev/v3/core-concepts/canonical-registration-and-discovery.html>
- Permissions, and row level filtering:
  <https://vueda.dev/v3/core-concepts/permission-model.html>,
  <https://vueda.dev/v3/core-concepts/row-level-permission-filtering.html>
- Building a CRUDL surface: <https://vueda.dev/v3/guides/create-crudl-surface.html>
- Component, REST, and Python API reference: <https://vueda.dev/v3/reference/>
- Glossary: <https://vueda.dev/v3/reference/glossary.html>

When VUEDA behaviour surprises you, check the docs before calling it a framework
gap. If the docs are wrong or silent, that is worth reporting as a docs issue
rather than working around silently.

## Architecture

- `server/` is a Django app that depends on the VUEDA server package, and
  `client/` is a Vue 3 and Vite app that depends on the VUEDA client package.
  Both resolve from their registries by default; a contributor working on VUEDA
  itself may point them at a local checkout, which is a local-only change.
- The server exposes Widget Warehouse catalog models through VUEDA serializers,
  filtersets, routers, and viewsets.
- The client uses VUEDA CRUD routing and falls back to `DefaultView*.vue`
  components when model-specific views are not present.
- Custom code should make VUEDA integration patterns clear. Keep customization
  examples realistic and easy to trace back to the VUEDA surface they exercise.

## Commit Message Style

Use the repo commitlint configuration based on Conventional Commits. Valid
types:

```text
build, ci, chore, content, docs, feat, fix, perf, refactor, remove, revert, style, test, wip
```

Example:

```text
docs(AGENTS): add workspace guidance
```

The scope should reference the affected filename without extension, module, or
concern.

## Committing

- Do not run `git commit`. Suggest a commit message instead.
- Do not use words with a leading `@` in commit messages. GitHub interprets
  those as user mentions.

## Writing Style

Avoid em dashes and en dashes. Use parentheses, periods, semicolons, colons, or
"to" in ranges instead.

## Lefthook

Configuration lives in `lefthook.yml`. When editing hook commands:

- Prefer lefthook's staged-file features over manual `git diff` pipelines.
- Use `glob:`, `root:`, `exclude:`, `{staged_files}`, and `stage_fixed: true`
  where appropriate.
- Do not add unnecessary "no matching files" guards. Lefthook skips commands
  automatically when no files match.
