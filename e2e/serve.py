"""
Start the Django server the end-to-end tests run against, on data of its own.

Playwright runs this from ``server/`` through ``uv run``. It never touches the
development database, cache keys, or uploaded files: ``reset_demo`` truncates the catalog
and deletes uploads, so pointing it at a developer's own configuration would destroy that
developer's data.

- The database is ``E2E_DATABASE_URL`` when set. Otherwise it is the configured
  ``DATABASE_URL`` with ``_e2e`` appended to the database name, created on first run.
- Cache keys take their own prefix, uploads go under ``e2e/.run/media``, and the allowed
  origin is the test client's.

Then it migrates, resets the demo to its seeded state, and serves. Every run starts from
the same data, which is what lets the specs name seeded orders and totals.
"""

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg
from psycopg import sql
from vueda.core.config import TomlEnv, load_toml

SERVER_DIR = Path.cwd()
E2E_DIR = Path(__file__).resolve().parent
SERVER_PORT = os.environ.get("E2E_SERVER_PORT", "8100")
CLIENT_ORIGIN = f"http://localhost:{os.environ.get('E2E_CLIENT_PORT', '8180')}"
CACHE_KEY_PREFIX = "widget-warehouse-e2e"


def configured(key, default=None):
    """Read a key the way ``config.settings.base`` does: environment, then local, then shared."""
    env = TomlEnv({**load_toml(SERVER_DIR / "config.toml"), **load_toml(SERVER_DIR / "config.local.toml")})
    return env(key, default)


def e2e_database_url():
    if os.environ.get("E2E_DATABASE_URL"):
        return os.environ["E2E_DATABASE_URL"]
    parts = urlsplit(configured("DATABASE_URL"))
    name = parts.path.lstrip("/")
    return urlunsplit(parts._replace(path=f"/{name}_e2e"))


def ensure_database(url):
    """Create the database if it does not exist, connecting to the server's maintenance database."""
    parts = urlsplit(url)
    name = parts.path.lstrip("/")
    maintenance = urlunsplit(parts._replace(path="/postgres"))
    with psycopg.connect(maintenance, autocommit=True) as connection:
        exists = connection.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
        if not exists:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
            print(f"[e2e] created database {name}", flush=True)


def e2e_cache_url():
    parts = urlsplit(configured("CACHE_URL", "redis://127.0.0.1:6379/0"))
    query = dict(parse_qsl(parts.query))
    query["key_prefix"] = CACHE_KEY_PREFIX
    return urlunsplit(parts._replace(query=urlencode(query)))


def main():
    database_url = e2e_database_url()
    ensure_database(database_url)
    media_root = E2E_DIR / ".run" / "media"
    media_root.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.local",
        "DATABASE_URL": database_url,
        "CACHE_URL": e2e_cache_url(),
        "MEDIA_ROOT": str(media_root),
        "ALLOWED_HOSTS": "localhost,127.0.0.1",
        "FRONTEND_DOMAIN": CLIENT_ORIGIN,
        "CSRF_TRUSTED_ORIGINS": CLIENT_ORIGIN,
        "CORS_ALLOWED_ORIGINS": CLIENT_ORIGIN,
    }

    def manage(*args):
        subprocess.run([sys.executable, "manage.py", *args], env=env, check=True)

    manage("migrate", "--noinput")
    manage("reset_demo", "--noinput")

    # The explicit config file keeps gunicorn from loading server/gunicorn.conf.py, which a
    # developer may have set up for TLS on their own machine.
    gunicorn = [
        sys.executable,
        "-m",
        "gunicorn",
        "config.asgi",
        "-k",
        "asgi",
        "--config",
        str(E2E_DIR / "gunicorn.conf.py"),
        "--bind",
        f"127.0.0.1:{SERVER_PORT}",
    ]
    os.execve(sys.executable, gunicorn, env)


if __name__ == "__main__":
    main()
