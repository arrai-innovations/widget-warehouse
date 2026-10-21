# Widget Warehouse

Widget Warehouse is a working example of [VUEDA](https://vueda.dev/v3/), using a
catalog, inventory, suppliers, and purchase orders to demonstrate forms, filtering,
permissions, workflows, and custom views.

Try the [hosted demo](https://www.widgetwarehouse.com/), or run the same application
locally.

## Where to start

- **Demo visitors:** follow the [walkthrough](https://www.widgetwarehouse.com/walkthrough/)
  for demo accounts, the replenishment exercise, and other features to explore.
- **Developers running this project:** follow [Local development](#local-development)
  for configuration, setup, and checks.
- **VUEDA integrators:** see [Integration examples](#integration-examples) for the
  code and framework features behind the demo.
- **Demo operators:** see [Demo operations](docs/demo-operations.md) for seeding,
  release tagging, deployment, and resets.

The repository's CircleCI deployment workflows operate the hosted demo using
Arrai Innovations infrastructure. Although the Arrai orbs are public, the workflows
assume Arrai-managed credentials and deployment services whose setup is not
documented here. They are not a supported deployment setup for VUEDA integrators.

## Local development

### Prerequisites and configuration

Install Python 3.12 to 3.14, Node.js 22 or newer, [uv](https://docs.astral.sh/uv/),
[pnpm](https://pnpm.io/), and [just](https://just.systems/). Start PostgreSQL with an
empty database and a role that can migrate it, and start Valkey or Redis for the
application cache. Running the server tests also requires permission to create a
test database.

See VUEDA's [Configure local settings](https://vueda.dev/v3/tutorials/start-building.html#configure-local-settings)
for the TOML configuration pattern. This repository already contains the application;
start with configuration rather than scaffolding a new project. Its frontend uses
port **8080**, and its server uses **8000**.

Create the ignored `server/config.local.toml` with your own values:

```toml
SECRET_KEY = "replace-with-a-unique-random-secret"
DATABASE_URL = "postgres://your-user:your-password@localhost:5432/widget_warehouse"
CACHE_URL = "redis://127.0.0.1:6379/0?key_prefix=widget-warehouse"
```

[server/config.toml](server/config.toml) supplies localhost origins.
[server/config.local.toml.example](server/config.local.toml.example) documents
additional settings; its hostname and filesystem examples target production.

For another hostname or HTTPS, configure the server origins in `config.local.toml`
and the client's `HTTPS_CERT_PATH`, `HTTPS_KEY_PATH`, `HMR_HOST`, `HMR_PORT`, and
`HMR_PROTOCOL` in an ignored `client/.env.development.local`. The server's optional
TLS configuration is illustrated in `server/gunicorn.conf.py.example`. See VUEDA's
[Local HTTPS development](https://vueda.dev/v3/guides/local-https-setup.html) for the
setup pattern.

### Install and run

Run these commands from the repository root:

```bash
just bootstrap
just manage migrate
just manage seed_demo
just serve
```

`seed_demo` creates the demo groups and users, attaches the purchase order workflow's
permissions to those groups, and then seeds the catalog, in one transaction. Open
<http://localhost:8080/> and choose **Follow the walkthrough** for the local guide
and demo accounts.

After changing demo permissions, run `just manage seed_demo` again and sign out
and back in. To discard local catalog changes and restore the demo data, run
`just manage reset_demo`. It asks for confirmation and deletes catalog records,
orders, their history, and uploaded catalog files before reseeding.

### Development commands

| Command                 | Purpose                                              |
| ----------------------- | ---------------------------------------------------- |
| `just check`            | Check server and client formatting and lint.         |
| `just test`             | Run server and client tests.                         |
| `just build`            | Build the production client.                         |
| `just preview`          | Preview the production client with the local server. |
| `just manage <command>` | Run a Django management command.                     |

Use `just test-server <args>` or `just test-client <args>` for focused tests; paths
are relative to the package directory. Package guidance is in
[server/AGENTS.md](server/AGENTS.md) and [client/AGENTS.md](client/AGENTS.md).

## Integration examples

The [integration guide](docs/integration-examples.md) connects the demo to its
implementation: metadata-driven navigation, workflow permissions, writable order
lines, warnings, totals, supplier-price defaults, and custom bulk actions.
[Dashboard charts](docs/dashboard-charts.md) describes the reports and chart components.

Use the [VUEDA documentation](https://vueda.dev/v3/) for framework contracts and API
reference, and this repository for examples of a consuming application.
