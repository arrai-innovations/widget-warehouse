# Widget Warehouse

Widget Warehouse is a working example of [VUEDA](https://vueda.dev/v3/), using a
catalog, inventory, suppliers, and purchase orders to demonstrate forms, filtering,
permissions, workflows, and custom views.

Try the [hosted demo](https://www.widgetwarehouse.com/), or run the same application
locally.

## Where to start

- **Demo visitors:** choose a [demo account](#demo-accounts), then follow
  [Create and approve a replenishment order](#create-and-approve-a-replenishment-order).
  [Explore the demo](#explore-the-demo) covers dashboards and other forms.
- **Developers running this project:** follow [Local development](#local-development)
  for configuration, setup, and checks.
- **VUEDA integrators:** see [Integration examples](#integration-examples) for the
  code and framework features behind the demo.
- **Demo operators:** see [Demo operations](docs/demo-operations.md) for seeding,
  deployment, and resets.

## Demo accounts

The sign-in page lists these accounts. Select one to fill the form, then sign in.
Every account uses the password `widget-demo`.

| Role                 | Email                          | What you can do                                                                                                                                                                        |
| -------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Inventory clerk      | clerk@widgetwarehouse.com      | Browse catalog, inventory, and warehouses; maintain suppliers and supplier prices; create purchase orders, edit drafts, and submit them for approval.                                  |
| Inventory supervisor | supervisor@widgetwarehouse.com | Everything the clerk can do; update inventory counts and targets; edit orders in any state; approve, reject, receive, or cancel orders; delete orders, suppliers, and supplier prices. |
| Sales associate      | associate@widgetwarehouse.com  | Browse catalog, inventory, warehouses, and promotions.                                                                                                                                 |
| Sales manager        | manager@widgetwarehouse.com    | The same read-only access as the sales associate.                                                                                                                                      |
| Accountant           | accountant@widgetwarehouse.com | Browse all catalog models and purchasing reports, without changing records or running transitions.                                                                                     |

To switch roles, choose **Sign Out** in the sidebar, then select another account.
Record the stock item and order reference you are working with so you can find them
after signing in again. Menus and available actions change with the account.

The hosted demo is shared: other visitors can change the same records, and operator
resets discard demo changes. Use sample data only. The walkthrough creates a shortage
from the current stock and order quantities, so it does not require a fresh reset.

## Create and approve a replenishment order

This walkthrough sets a stock target, creates a purchase order for the resulting
shortage, and approves that order. It ends with approved incoming stock covering the
shortage. **On-hand stock does not increase:** the receive transition only records a
workflow state, and stock posting and partial receipts are not implemented.

### Create a shortage as the supervisor

1. Sign in as **Inventory supervisor** and open **Inventory Records**. Choose an
   existing stock item, such as `SPR-B003-STD @ SYD-DC`. You can use another item with
   an active product, an active warehouse, and an active, approved supplier. Use
   pagination or set **Rows per page** to **100** to find the example item.
2. Select its list checkbox and choose **Replenish**. Read **On hand** and both
   numbers under **Incoming / Pending**. Add those three quantities to get the
   stock already held or on order. The preview shows them even when the item does
   not need replenishment. Do not create an order yet.
3. Return to **Inventory Records** and edit that item. Set **Reorder threshold**
   to the total from the preview plus **10**, and **Max stock level** to that total
   plus **20**. Leave **Quantity on hand** unchanged and choose **Submit** to save.
   On an edit form, **Submit** saves fields; on the order list, **Submit** starts
   the approval workflow. For example, with 5 on hand, 12 incoming, and 8 pending,
   set the threshold to **35** and the maximum to **45**. This represents a higher
   stock requirement and creates a shortage beyond what existing orders cover.
4. Open **Review shortages**, or the dashboard's **Below reorder** tile. Your item
   is now in this filtered queue. Keep its stock-item label for the next account.

### Create a draft as the clerk

1. Switch to **Inventory clerk**. Open **Inventory Records**, choose **Review
   shortages**, and select the same item. The clerk can read its stock and targets
   but cannot edit them.
2. Choose **Replenish**. The proposed quantity is **20**, accounting for both
   existing pending orders and approved incoming stock. The page groups selected
   items by supplier and destination warehouse; select additional items if you
   want to see multiple groups.
3. Keep the proposed quantity for this walkthrough. You can edit **Unit price**;
   enter a sample price if none is stored. Choose **Create 1 draft purchase order**
   (the count changes when selecting multiple groups). The order list opens
   filtered to your new batch. Note the new order's **Reference**; **Show all
   orders** removes the batch filter.
4. Edit the draft to explore its order lines. To try a delivery warning, check the
   supplier's **Typical lead days** and choose an **Expected arrival date** earlier
   than that lead time after the **Order date**. For a supplier with a lead time
   greater than one day, use the next day. Save, then cancel the warning
   confirmation: the edit remains unsaved. Save again and confirm to keep the
   earlier date.
5. Return to the order list, select your draft, and choose **Submit** in the selection bar.
   On the confirmation page, choose **Yes, continue** to submit it for approval.
   The clerk can still read the submitted order, but its edit action is gone.

If another visitor changes stock, prices, or orders while you are working, the
proposal can become stale. Choose **Reload proposals** and review it again. If
existing orders now cover the threshold, repeat the supervisor's target calculation
using the latest quantities. If the preview reports an inactive product or warehouse,
choose another stock item; an inventory role can correct an inactive or unapproved
supplier through **Suppliers**. No instance reset is needed.

### Approve the order as the supervisor

1. Switch to **Inventory supervisor**. Open **Purchase Orders** and find the reference
   you recorded. Select the submitted order, choose **Approve**, then confirm with
   **Yes, continue**.
2. Return to **Inventory Records**, select the same stock item, and choose
   **Replenish**. The order quantity has moved from **Pending** to **Incoming**.
   The preview explains that existing orders cover the threshold and proposes no
   further purchase.
3. The item still appears under **Below reorder**, because that queue compares
   on-hand stock with the threshold. Approval covers the purchasing requirement;
   it does not record a physical delivery.

To explore rejection instead, choose **Reject** on a submitted order. It returns to
**Draft**, and the clerk can edit and submit it again. Only the supervisor can approve
or reject an order.

### Try a stock-count warning

While signed in as **Inventory supervisor**, edit the same inventory record. Note its
original **Quantity on hand**, then enter one unit above **Max stock level** and save.
The warning asks you to confirm the count. Cancel to leave stored stock unchanged.
To try confirmation too, save again and confirm, then restore the original quantity.
Both stock and delivery warnings are advisory: confirmation permits the save.

## Explore the demo

- **Dashboard:** compare the supervisor and sales associate accounts. Tiles follow
  each role's read permissions and open filtered lists. Purchasing reports are
  available to the inventory roles and accountant. Change the pipeline period or
  supplier-chart period, then follow a chart link to its matching orders.
- **Order totals:** filter Purchase Orders by supplier and watch the **Order value**
  footer follow the entire filtered result, not just the visible page. Values have
  no currency designation because the catalog does not store one.
- **Suppliers and prices:** either inventory role can edit supplier details,
  including multiple notification email addresses, approval, and typical lead time.
  **Supplier Prices** supplies default prices for new order lines. Editing a line's
  price does not change its supplier price, and changing a supplier price does not
  rewrite existing orders.
- **Read-only browsing:** use either sales account to explore promotions and their
  date ranges, or the accountant to see both suppliers and promotions without write
  actions. Widgets, categories, variants, warehouses, and promotions are read-only
  for all demo accounts.

## Local development

### Prerequisites and configuration

Install Python, Node.js 22 or newer, [uv](https://docs.astral.sh/uv/),
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
just manage seed_demo_users
just manage seed_workflows
just manage seed_catalog
just serve
```

Keep the seed order: users create the groups, workflows attach permissions to those
groups, and catalog orders receive their initial workflow states. Open
<http://localhost:8080/> and use the same [demo accounts](#demo-accounts) and walkthrough.

After changing demo permissions, run `just manage seed_demo_users` again and sign out
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
