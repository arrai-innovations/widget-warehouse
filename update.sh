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

# A fresh deployment is migrated but empty, and the sign-in view lists five demo accounts
# that do not exist until this has run. It is idempotent and converges, so a deploy can run
# it unconditionally: it restores the seeded rows to their seeded values without
# discarding anything an evaluator is part way through. Returning the demo to its starting
# state is `reset_demo`, which the scheduled reset runs and a deploy deliberately does not.
uv run --no-sync python server/manage.py seed_demo
