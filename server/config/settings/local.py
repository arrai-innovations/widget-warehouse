from config.settings.base import *  # noqa: F403

DEBUG = True

CSRF_COOKIE_NAME = "widget-warehouse-csrf-token"

CORS_ALLOW_CREDENTIALS = True

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# Must be imported after settings are fully resolved so PERMISSION_NAMES_MAPPING
# is available when patch_django reads it.
from vueda.core import patch_django  # noqa: F401, E402
