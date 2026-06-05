# Widget Warehouse Server Guide

This directory contains the Widget Warehouse Django server. It consumes the
local editable VUEDA server package from `../../vueda/server`.

## Commands

Run these from the repo root unless a command explicitly says otherwise:

- Install dependencies: `just bootstrap`
- Check server: `just check-server`
- Fix server: `just fix-server`
- Test server: `just test-server`
- Serve server only: `just serve-server`
- Django management command: `just manage <command>`

Useful direct commands from `server/`:

```bash
uv run --no-sync pytest
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync python manage.py makemigrations
uv run --no-sync python manage.py migrate
```

## Architecture

- Django project config: `config/`
- Main package: `widget_warehouse/`
- Catalog app: `widget_warehouse/catalog/`
- User app: `widget_warehouse/users/`
- Tests: `tests/`

The catalog app models widgets, suppliers, warehouses, inventory records, and
promotions. API exposure follows the VUEDA pattern:

- `models.py` defines Django models using VUEDA base classes.
- `serializers.py` defines VUEDA serializers and field adapters.
- `filtersets.py` defines query filtering.
- `viewsets.py` exposes VUEDA viewsets.
- `routers.py` and `urls.py` wire routes.

## Code Style

- Python 3.11 or newer.
- Ruff enforces line length 120, import sorting, pyupgrade, bugbear, simplify,
  and Ruff-specific rules.
- Use Django and DRF conventions for models, serializers, filtersets, viewsets,
  migrations, and management commands.
- Keep model and serializer changes in sync with the client CRUD metadata that
  VUEDA consumes.
- When changing models, create migrations unless the user explicitly asks not
  to.

## VUEDA Integration

- Prefer VUEDA base classes such as `VuedaModel`, `Lookup`,
  `VuedaSerializer`, `VuedaLookupSerializer`, and `VuedaViewSet` when adding
  catalog surfaces.
- Serializer fields determine what the client can render and edit through
  VUEDA CRUD views.
- Filtersets and viewsets affect list behavior, search, and client-visible
  actions.
- File, image, range, duration, and relation fields may need explicit VUEDA
  serializer field adapters.

## Testing

- Use pytest through `just test-server`.
- Add or update tests when changing model behavior, serializer validation,
  filter behavior, permissions, or routes.
- For schema or metadata changes, verify the client impact as part of the
  change summary.
