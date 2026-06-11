bootstrap:
  cd {{justfile_directory()}} && pnpm install
  pnpm -C {{justfile_directory()}} exec lefthook install
  cd {{justfile_directory()}} && uv sync --all-groups --all-packages

check:
  pnpx concurrently -n server,client -c green,cyan "just check-server" "just check-client"

check-server:
  cd {{justfile_directory()}}/server && uv run --no-sync ruff check . && uv run --no-sync ruff format --check .

check-client:
  cd {{justfile_directory()}}/client && pnpm run lint && pnpm run format

fix:
  pnpx concurrently -n server,client -c green,cyan "just fix-server" "just fix-client"

fix-server:
  cd {{justfile_directory()}}/server && uv run --no-sync ruff check --fix . && uv run --no-sync ruff format .

fix-client:
  cd {{justfile_directory()}}/client && pnpm run eslint && pnpm run prettier

test:
  pnpx concurrently -n server,client -c green,cyan "just test-server" "just test-client"

test-server:
  cd {{justfile_directory()}}/server && uv run --no-sync pytest

test-client:
  cd {{justfile_directory()}}/client && pnpm test run

manage *args:
  cd {{justfile_directory()}}/server && uv run --no-sync python manage.py {{args}}

serve:
  pnpx concurrently -n server,client -c green,cyan "just serve-server" "just serve-client"

serve-server:
  cd {{justfile_directory()}}/server && uv run --no-sync gunicorn config.asgi -k asgi --reload --bind 0.0.0.0:8000 --keyfile /etc/pki/tls/private/arrai.com.key --certfile /etc/pki/tls/certs/arrai.com.crt

serve-client:
  cd {{justfile_directory()}}/client && pnpm run dev -- --force