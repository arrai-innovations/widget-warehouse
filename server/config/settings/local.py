from config.settings.base import *  # noqa: F403

DEBUG = True

# The makeviewmigration command, used to author the database views behind the unmanaged
# summary models. It is a development tool: the migrations it writes read the committed
# .sql files, so a deployment never installs or lists this app.
INSTALLED_APPS = [*INSTALLED_APPS, "django_view_manager.utils"]  # noqa: F405

CORS_ALLOW_CREDENTIALS = True

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# Must be imported after settings are fully resolved so PERMISSION_NAMES_MAPPING
# is available when patch_django reads it.
from vueda.core import patch_django  # noqa: F401, E402
