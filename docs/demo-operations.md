# Demo operations

This guide is for operators of the Arrai Innovations hosted demo. The CircleCI
workflows in `.circleci/` depend on Arrai-managed credentials and deployment
services. The Arrai orbs are public, but the supporting infrastructure is assumed
and its setup is not documented here. These workflows are not a supported
deployment setup for VUEDA integrators.

## Release and deploy

Server and client releases are independent. Merging to `main` runs the applicable
tests; pushing a release tag triggers deployment to production for that component.
Use `server-v<version>` for the server and `client-v<version>` for the client.

Before tagging, bump the version for each component being released:

- Server: update `server/pyproject.toml`, then run `uv lock` from the repository
  root to update the workspace package version in `uv.lock`.
- Client: update `client/package.json`. The release pipeline checks that the tag's
  version matches this field, which is also embedded in the built client.

Include runtime dependency updates when deciding which components to release.
Client dependencies can change through `pnpm-lock.yaml` and `pnpm-workspace.yaml`
without changes to client source. Deploying the server does not rebuild or deploy
the client.

Commit the version changes and merge them to `main`. Wait for the applicable CI
tests to pass, then update your local `main` and confirm it contains the changes
you intend to release:

```bash
git switch main
git pull --ff-only
git status --short
git log -5 --oneline
```

From a clean checkout, create and push only the tags for the components being
released. For example, when releasing version `0.2.1` of both components:

```bash
git tag -a server-v0.2.1 -m "Server 0.2.1"
git tag -a client-v0.2.1 -m "Client 0.2.1"
git push origin server-v0.2.1 client-v0.2.1
```

Choose unused versions; do not move an existing release tag. The two components
do not need to have the same version.

The server tag pipeline runs server tests, then asks the production deployer to
check out the tag and run `update.sh`. The client tag pipeline runs client tests,
builds the client, publishes `dist.zip` as a GitHub release asset, then asks the
production deployer to install that bundle.

Follow the tag pipelines in CircleCI through `server-deploy-production` and
`client-release-production`. After they succeed, check the hosted demo's sign-in
and the affected functionality. A pushed tag alone does not confirm deployment.

### Retry a failed deployment

If tests and any client build and release succeeded but deployment failed, fix the
deployment configuration on `main`, then send the existing tag to the deployer
again:

```bash
just redeploy server-v0.2.1
just redeploy client-v0.2.1
```

Run only the command for the failed component. This uses pipeline configuration
from `main`, skips tests and builds, and deploys the existing tag. A client retry
requires the tag's GitHub release to already contain `dist.zip`. It cannot include
new application or dependency changes; release those under a new version.

Authenticate with `circleci setup` or set `CIRCLECI_TOKEN`. Client retries also
require an authenticated `gh` CLI to check the release asset. The command prints
the CircleCI pipeline URL; follow it and check the demo after deployment.

## Seed

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
