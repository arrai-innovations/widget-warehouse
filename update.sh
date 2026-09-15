#!/usr/bin/env bash
set -e

# The `vueda` CLI defaults DJANGO_SETTINGS_MODULE to config.settings.local when it is
# unset, and that module forces DEBUG on. Under those settings an update installs dev
# dependencies and skips collectstatic, so name the deployment's settings module here.
export DJANGO_SETTINGS_MODULE=config.settings.production

uv run --no-sync vueda update --non-interactive

# The production cache is DatabaseCache, whose table is created outside the migration
# graph. This is idempotent, and it runs after `vueda update` has migrated. Without the
# table, the password reset cooldown raises on every attempt.
uv run --no-sync python server/manage.py createcachetable
