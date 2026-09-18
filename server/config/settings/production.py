import logging

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from vueda.core.default_settings import get_production_defaults

from config.settings.base import *  # noqa: F403
from config.settings.base import LOGGING as BASE_LOGGING
from config.settings.base import env

# Requires SENTRY_DSN, which has no default. A deployment that omits it fails at startup.
production_settings = get_production_defaults(env)
locals().update(production_settings)

# DEBUG is false by default, but state it here as well. `vueda update` reads it to decide
# whether to install dev dependencies and whether to run collectstatic at all, so a
# deployment config that set it true would quietly change what a deploy does.
DEBUG = False

# Share sessions, password reset cooldowns, and rate limits across worker processes.
# Valkey uses Django's Redis backend. Deployments can override the address and key
# prefix through CACHE_URL in config.local.toml or the environment.
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
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# Django's own clickjacking header, which VUEDA's default middleware list omits. Nothing in
# this project is meant to be framed, and the built client is served by the web server
# rather than through here.
MIDDLEWARE = [*MIDDLEWARE, "django.middleware.clickjacking.XFrameOptionsMiddleware"]  # noqa: F405

# SECURE_SSL_REDIRECT stays off, so `check --deploy` reports security.W008. The web server
# owns the HTTP to HTTPS redirect. Turning it on here would add a second redirect that
# depends on the proxy sending X-Forwarded-Proto, and a proxy that stopped sending it would
# put the site in a redirect loop rather than merely losing a redirect.
#
# SECURE_HSTS_INCLUDE_SUBDOMAINS and SECURE_HSTS_PRELOAD also stay off (security.W005 and
# security.W021). Both commit every widgetwarehouse.com subdomain to HTTPS, which is a
# decision about the domain rather than about this deployment.

# Hash static filenames so a deploy cannot serve a stale asset out of a browser or proxy
# cache. collectstatic fails on a reference it cannot resolve, which is the point: a broken
# reference stops the deploy instead of reaching visitors.
STORAGES = {
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}

# Send application logs to the rotating file handler VUEDA already defines, which writes to
# LOGS_FOLDER. Console output would land in the journal mixed with gunicorn's own, and the
# file is where the other arrai deployments keep theirs. Copy rather than mutate, so the
# base module's dict is left alone.
LOGGING = {**BASE_LOGGING, "root": {**BASE_LOGGING["root"], "handlers": ["file"]}}

sentry_sdk.init(
    dsn=production_settings["SENTRY_DSN"],
    integrations=[
        LoggingIntegration(level=production_settings["SENTRY_LOG_LEVEL"], event_level=logging.ERROR),
        DjangoIntegration(),
    ],
    environment=production_settings["SENTRY_ENVIRONMENT"],
    traces_sample_rate=production_settings["SENTRY_TRACES_SAMPLE_RATE"],
)

# Must be imported after settings are fully resolved so PERMISSION_NAMES_MAPPING is
# available when patch_django reads it. Nothing else applies the patch, so a settings
# module that omits this import leaves Django unpatched.
from vueda.core import patch_django  # noqa: F401, E402
