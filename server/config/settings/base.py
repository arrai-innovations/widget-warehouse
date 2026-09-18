from pathlib import Path

from vueda.core.config import TomlEnv, load_toml
from vueda.core.default_settings import get_defaults

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
APPS_DIR = ROOT_DIR / "widget_warehouse"

env = TomlEnv(
    {
        **load_toml(ROOT_DIR / "config.toml"),
        **load_toml(ROOT_DIR / "config.local.toml"),
    }
)

default_settings = get_defaults(env)
locals().update(default_settings)

# Valkey through Django's Redis backend, in every deployment including a developer's
# machine. A cache here is shared state, not a local optimization: sessions, the password
# reset cooldown, and rate limits all live in it, and LocMemCache is per-process, so an
# ASGI server's workers would each answer from a cache the others cannot see. Running the
# same backend locally is also what keeps a cache bug reproducible off production.
# Deployments override the address and key prefix through CACHE_URL.
CACHES = {
    "default": env.dj_cache_url(
        "CACHE_URL",
        default={
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": "redis://127.0.0.1:6379/0",
            "KEY_PREFIX": "widget-warehouse",
        },
    )
}
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# The client reads this cookie by name through VITE_CSRF_COOKIE_NAME, so every settings
# module has to agree on it.
CSRF_COOKIE_NAME = "widget-warehouse-csrf-token"

# Imported after get_defaults() so PERMISSION_NAMES_MAPPING is already set. If you
# override PERMISSION_NAMES_MAPPING in a child settings module (e.g. local.py,
# production.py), re-import patch_django there after the customization.
INSTALLED_APPS = [*default_settings["INSTALLED_APPS"], "widget_warehouse.catalog"]

REST_FRAMEWORK = {**REST_FRAMEWORK, "PAGE_SIZE": 10}  # noqa: F821
