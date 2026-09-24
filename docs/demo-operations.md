# Demo operations

## Seed and deploy

Run from the repository root after migrations:

```bash
just manage seed_demo
```

The command is idempotent. It seeds the demo users, then the purchase order workflow,
then the catalog, in one transaction: the workflow looks the users' groups up by name,
and a purchase order cannot be saved until its workflow exists. Each run reapplies group
permissions and resets the published account passwords.

Reseeding updates seeded catalog values, but preserves existing order workflow states.
Supplier prices are created only when absent, so price changes survive reseeding.
Rows created by visitors and uploaded files remain until explicitly removed or reset.

`update.sh` runs `seed_demo` during deployment after the deployment tool's migration
step. Deployment does not run `reset_demo`.

## Reset

To discard demo changes and restore the seeded scenario:

```bash
just manage reset_demo
```

This deletes catalog rows, purchase orders, workflow states for those orders, their
history, and uploaded catalog files, then runs the three seeds. Seeded IDs remain
stable, so bookmarked seeded detail URLs still resolve. Accounts outside the five
published demo users and the workflow definition are retained.

The command asks for confirmation. A scheduled production reset can use `--noinput`
from the deployment checkout, with production settings:

```bash
DJANGO_SETTINGS_MODULE=config.settings.production uv run --no-sync python server/manage.py reset_demo --noinput
```

Choose the schedule in the deployment environment and communicate it to visitors.
The repository does not configure the host's scheduler. Resets interrupt work on shared
records; the walkthrough creates its own shortage and does not depend on a visitor
being able to reset the instance.

## Seeded scenario

The catalog includes purchase orders across Draft, Submitted, Approved, Received, and
Cancelled, including overdue approved orders and stock below its reorder threshold.
A further 130 received orders provide 26 complete weeks of supplier purchasing history.
These historical orders do not change on-hand stock.

See [Local development](../README.md#local-development) for configuration, and
[Dashboard charts](dashboard-charts.md) for the purchasing-history model.
