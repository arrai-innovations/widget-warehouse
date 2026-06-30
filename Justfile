# Treat recipe lines starting with `#` as justfile comments: don't echo them to
# stderr or pass them to the shell.
set ignore-comments := true

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

build: build-client

build-client:
  cd {{justfile_directory()}}/client && pnpm run build

preview: build-client
  pnpx concurrently -n server,client -c green,cyan "just serve-server" "just preview-client"

preview-client:
  cd {{justfile_directory()}}/client && pnpm run preview

manage *args:
  cd {{justfile_directory()}}/server && uv run --no-sync python manage.py {{args}}

serve:
  pnpx concurrently -n server,client -c green,cyan "just serve-server" "just serve-client"

serve-server:
  # TLS is opt-in and machine-specific: copy server/gunicorn.conf.py.example to
  # server/gunicorn.conf.py and set certfile/keyfile there. gunicorn auto-loads
  # that file from the server/ directory. With no such file, this serves HTTP.
  cd {{justfile_directory()}}/server && uv run --no-sync gunicorn config.asgi -k asgi --reload --bind 0.0.0.0:8000

serve-client:
  cd {{justfile_directory()}}/client && pnpm run dev -- --force
