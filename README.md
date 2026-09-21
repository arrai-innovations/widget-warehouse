# Widget Warehouse

[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json)](https://github.com/copier-org/copier)

Widget Warehouse is a working example application for VUEDA. It is intended to
exercise VUEDA features across realistic catalog, inventory, supplier, user,
file, range, relation, and CRUD workflows.

The project also demonstrates customization possibilities for consuming VUEDA
applications, including custom client views, routing, styling, serializers,
filtersets, server metadata, and app-specific behavior layered on top of VUEDA.

## Bootstrap

```bash
just bootstrap
```

## Run for Local Development

```bash
just serve
```

## Seed the Demo Data

```bash
just manage seed_demo_users
just manage seed_workflows
just manage seed_catalog
```

Run them in that order the first time. `seed_workflows` attaches state permissions to the
demo groups, so it needs `seed_demo_users` to have created them.

All three are idempotent, so a deployed instance can be reseeded at any time. Supplier
prices are created when absent and retain evaluator edits until a reset. Reseeding
does not walk an order back: `seed_catalog` puts an order into its seeded workflow state
when it creates the order and not afterwards, and `seed_workflows` only gives a starting
state to orders that have none, which is what backfills orders seeded before the workflow
existed. `seed_demo_users` resets each demo password on every run, so the credentials on
the sign-in view always work.

The seeded orders are spread across the pipeline rather than all left in draft: three
drafts waiting to be submitted, two waiting for approval, three approved (two of them
already past their expected arrival), three received, and one cancelled. A further 130
received orders provide 26 complete weeks of deterministic supplier purchasing history. Some seeded stock
sits under its own reorder threshold for the same reason. Both are shapes the demo is
meant to show, so `server/tests/test_seed_catalog.py` pins them.

## Reset the Demo

```bash
just manage reset_demo
```

Reseeding restores what it seeded, but it cannot undo. A row an evaluator created stays, an
uploaded datasheet stays, and an order walked from draft to approved stays approved, since
`seed_workflows` only gives a starting state to orders that have none. A public instance
therefore runs out of drafts to submit, which is the moment the walkthrough is built around.

`reset_demo` is the undo half. It discards every catalog row, the purchase orders and their
workflow states, the history behind them, and the uploaded files, then runs the three seeds
in order. The seeded ids are stable from one reset to the next, so a bookmarked detail URL
still resolves afterwards. Accounts outside the five demo users are left alone, including
the superuser, and so is the workflow definition, which `seed_workflows` converges on
anyway.

Pass `--noinput` to skip the confirmation prompt. That is how a scheduled reset of the
public instance runs it, from the server's deployment checkout (`SERVER_DIR` on the
deployer):

```cron
0 4 * * * cd $SERVER_DIR && DJANGO_SETTINGS_MODULE=config.settings.production uv run --no-sync python server/manage.py reset_demo --noinput
```

A deploy does not reset. `update.sh` runs the three seeds so a fresh deployment has a demo
to sign in to, and leaves an evaluator part way through an order alone.

## Demo Roles

Five groups and one user per group are seeded as data by `seed_demo_users`, not as
fixtures and not through the DEBUG-only permission overview UI, so the whole matrix
reproduces on deploy. Every account uses the password `widget-demo`, and the sign-in
view lists them so an evaluator can switch roles without leaving the page.

| Group                  | Sign in as                     | Reads                                                 | Writes                                  | Transitions                                        |
| ---------------------- | ------------------------------ | ----------------------------------------------------- | --------------------------------------- | -------------------------------------------------- |
| `inventory-clerk`      | clerk@widgetwarehouse.com      | catalog, inventory, suppliers, warehouses             | suppliers, purchase order drafts        | `submit`                                           |
| `inventory-supervisor` | supervisor@widgetwarehouse.com | catalog, inventory, suppliers, warehouses             | suppliers, purchase orders in any state | `submit`, `approve`, `reject`, `receive`, `cancel` |
| `sales-associate`      | associate@widgetwarehouse.com  | catalog, inventory, warehouses, promotions, customers | sales order drafts                      | `submit`                                           |
| `sales-manager`        | manager@widgetwarehouse.com    | catalog, inventory, warehouses, promotions, customers | sales orders in any state               | `submit`, `approve`, `reject`, `ship`              |
| `accountant`           | accountant@widgetwarehouse.com | everything                                            | nothing                                 | none, plus a bulk export action                    |

Customers and sales orders are not modelled yet, so the two sales roles are still
read-only and grant the same access as each other. Purchase orders are modelled and have
a workflow: the clerk creates and edits drafts, the supervisor edits an order in any
state and takes every approval decision, and only the supervisor can delete one.

Suppliers follow the same split without a workflow. Both inbound roles add and edit a
vendor, and only the supervisor can delete one. A Django permission names a model and an
action, so the split stops there: `is_approved` reads as a supervisor decision, but a
role that may update a supplier may set every field on it. Narrowing that to one field
would mean giving Supplier its own workflow, which is what the purchase order already
demonstrates.

What is live today is the Reads column. Sign in as the clerk and the sales associate in
turn: both get the same widgets, categories, variants, inventory records, and
warehouses, but only the clerk sees Suppliers and only the associate sees Promotions.
The navigation is not built per role in client code. It asks VUEDA for each model's
metadata, and VUEDA reports only the actions the signed-in user is permitted, so the
menu, the row actions, and the API all answer from one permission decision. Sign in as
the superuser to see every screen with create, update, and delete restored, including
the ones no demo role writes.

## The Dashboard

Signing in lands on `/dashboard/`, which is the same page for everybody and a different
page for every role. It shows work queues, an order pipeline, supplier purchasing trends, and catalog counts.

The tiles are declared once, in `client/src/views/ViewDashboard.vue`, and nothing on the
page asks who is signed in. Each tile asks VUEDA whether this account may list its model
and disappears when the answer is no, so the sales roles get the stock and promotion
queues while the inventory roles get the stock, order, and supplier queues, and only the
roles that can read orders see the pipeline and purchasing chart. Sign in as the supervisor and then as
the sales associate to watch the same page come back different.

Each tile is one list request for a single row: every VUEDA list response carries
`totalRecords` for the whole filtered set, so a count costs a page of one rather than an
endpoint of its own. The filter that produced the number is also the link the tile points
at, so opening a tile lands on the list it counted, already filtered. The pipeline defaults to orders placed in the last 30 days, including today; 90 days and
all time are also available. Each state link retains the selected date range. Its report
reuses the database view's workflow labels and ordering, but counts the caller's authorized,
filtered orders so states with no matching orders remain zero.

The supplier chart offers 6, 12, or 26 complete weeks of approved and received purchase
order value. Both charts use native Unovis components and VUEDA's optional theme stylesheet,
with separate chart colors. See [Dashboard chart integration](docs/dashboard-charts.md)
for the report contracts, request lifecycle, and palette assignments.

One tile reports a sum rather than a count. "Open order value" reads `columnTotals` from
the same envelope, because the order viewset declares `total_value` in `column_totals`, so
what the warehouse has committed to orders in flight arrives beside how many there are. It
shows a plain number: nothing in the catalog records a currency, so the page does not
invent one.

## Purchase Orders

A purchase order carries its lines as a writable inline, so one request creates or
updates the order and its line rows together. The client sends the `lines` expand on
create and update, which is what makes the nested payload deserialize as objects rather
than as ids; a line left out of an update is deleted. Sign in as the clerk and edit
`PO-1044`, one of the seeded drafts, to see it. The list view deliberately does not expand
the lines: it shows the supplier and destination warehouse instead.

The list also carries an `Order value` column and totals it in the footer. The value is not
a column on the order: the viewset annotates it as a sum over the order's lines, the
serializer declares a field of the same name and describes its type through
`get_field_model_info`, and VUEDA's `column_totals` sums it over the filtered queryset. So
the footer answers "what is this list worth" rather than "what is this page worth". Filter
by supplier and the total follows, and the column sorts on the server because the value is
a database expression rather than something computed per row. The inventory list totals
`quantity_on_hand` the same way.

## The Purchase Order Workflow

An order moves through five states. `seed_workflows` defines the whole thing as data, so
a deployed instance reproduces it by running the command; nothing here comes from
fixtures or from the DEBUG-only workflow management UI.

| Transition | From                             | To          | Run by                                    |
| ---------- | -------------------------------- | ----------- | ----------------------------------------- |
| `submit`   | `draft`                          | `submitted` | `inventory-clerk`, `inventory-supervisor` |
| `approve`  | `submitted`                      | `approved`  | `inventory-supervisor`                    |
| `reject`   | `submitted`                      | `draft`     | `inventory-supervisor`                    |
| `receive`  | `approved`                       | `received`  | `inventory-supervisor`                    |
| `cancel`   | `draft`, `submitted`, `approved` | `cancelled` | `inventory-supervisor`                    |

Three separate permission layers decide what a role may do, and they answer different
questions:

- A **workflow permission** gates the workflow as a whole. It is `read_purchaseorder`
  here, so whoever can read an order can see its transitions. The accountant can, and is
  then offered none, because no transition permission matches them.
- A **transition permission** makes one transition executable. The five above are ordinary
  Django permissions on the purchase order (`submit_purchaseorder` and so on), granted to
  groups by `seed_demo_users`. Holding one is not enough: the order also has to be in a
  state the transition starts from, which is why a supervisor cannot approve a draft.
- A **state permission** grants or denies a normal CRUDL permission for one state and one
  group. The clerk's baseline lets them update any purchase order; a deny rule on each
  state after `draft` takes that back, so the clerk edits drafts and nothing else.

That last rule is the one to see for yourself. Sign in as the clerk, open a draft order,
and edit it. Submit it, and the edit is gone: same order, same URL, same user, and the
affordance disappears because the row moved state. Rejecting it puts the order back in
`draft` and hands the clerk their edit back.

Available transitions appear in the client and are executed through VUEDA's action forms.

## Walkthrough: Replenish Stock

Start with the seeded demo and sign in as **Inventory clerk**
(`clerk@widgetwarehouse.com`, password `widget-demo`). This walkthrough follows a stock
shortage through purchasing and approval, using the same records across each step.

1. Open **Inventory Records** and choose **Review shortages** in the compact notice.
   The list filters to records below their reorder threshold and sorts by **Units below
   threshold**, largest first. Product SKUs identify the rows. The dashboard's **Below
   reorder** tile is another entry into this queue.
2. Select a few records using the ordinary list checkboxes, then choose **Replenish**
   in the selection bar. For a repeatable fresh-demo example, choose `SPR-B003-STD @ SYD-DC`
   and `GSK-B003-STD @ SYD-DC`. Include `BRG-6204-ZZ @ MEL-OVF` to see a shortage already
   covered by an existing order. Selection concerns the records you checked, not every
   record matching the filter.
3. Review the proposed orders, grouped by **supplier and destination warehouse**. Each
   stock item shows on-hand stock, its threshold and replenishment target, approved
   incoming stock, and pending quantities on draft or submitted orders. Existing orders
   count towards coverage, so a shortage is not automatically another purchase.
4. Adjust an order quantity or unit price. Defaults replenish to `max_stock_level`, or
   to the reorder threshold when no maximum exists, after subtracting on-hand and order
   coverage. When that coverage already reaches the threshold, no further purchase is
   proposed. Inactive products or warehouses, unapproved suppliers, and inconsistent
   stock targets explain why a row cannot be included. Missing supplier prices can be
   entered directly in the form.
5. Choose **Create N draft purchase orders**. The server checks the reviewed stock and
   order coverage again, then creates the whole batch together. The destination is the
   ordinary PO list restricted to the new batch. **Show all orders** removes that scope.
6. Edit one of the generated drafts before submitting it. Set **Expected arrival date**
   to one day after its **Order date**, then save. The seeded suppliers' typical lead
   times are longer than one day, so a field warning explains the early delivery and a
   confirmation dialog asks you to acknowledge it. Cancel the dialog first: the edit
   remains unsaved and the warning stays visible. Save again and confirm to keep the
   earlier date, as if expedited delivery had been arranged with the supplier.
7. Select that draft and choose **Submit** in the selection bar.
   Switch to **Inventory supervisor** (`supervisor@widgetwarehouse.com`) to approve it or reject it back to
   draft. The clerk can edit drafts but cannot approve them; submitting removes their
   edit permission until an order returns to draft.
8. Return to the inventory shortage and choose **Replenish** again. Its new draft or
   submitted order appears as pending coverage; after approval it appears as incoming.
   Creating a draft does not change on-hand stock. The current receive transition records
   workflow state only; automatic stock posting and partial receipts are not implemented.
9. If you have a **superuser** account, sign in with it to try the stock warning. The
   five demo roles can read inventory records but cannot edit them. Open **Inventory
   Records**, clear the shortage filter if needed, and edit `SPR-B003-STD @ SYD-DC`.
   Note its original **Quantity on hand**, then set it to one unit above its **Max stock
   level** and save. The warning asks you to confirm the count before saving stock above
   the maximum. Cancel to leave the stored count unchanged, or confirm to save it and
   then restore the original quantity so the shortage remains available for the demo.

These are advisory warnings: confirming allows the save, while cancelling leaves the
stored record unchanged. They use VUEDA's standard
[warning confirmation dialog](https://vueda.dev/v3/reference/api/vue/#formconfirmdialog).

Supplier prices are maintained through **Supplier Prices**. Both inventory roles can
maintain them; the accountant can read them and the sales roles cannot. Ordinary PO
create/update forms also default a newly selected variant from the chosen supplier's
price. Each PO line retains its own editable price: negotiating a line price does not
update the supplier price, and changing the supplier price does not rewrite older orders.

Reselecting a variant or changing the supplier looks up its price again. If no price is
stored, enter one on the order line. The API applies the same default when a new line
omits its price, while an explicitly supplied price (including zero) takes precedence.

For integrators, this is a custom bulk action composed with the standard list rather
than a separate selection screen. `InventoryRecordViewSet.replenish` exposes GET preview
and POST execution, and the client registers
`ViewActionCatalogInventoryrecordReplenish.vue` through `setCrudComponents`. The page uses `useForm`
and `ActionForm` for input and submission handling. The shared calculation and batch
creation live in `catalog/replenishment.py`; supplier-price defaults live in
`catalog/pricing.py` and `client/src/use/usePurchasePriceDefaults.js`.

The server supports VUEDA's `Dry-Run` header without creating orders or batch receipts.
Actual submissions use an idempotent batch identifier, and a stale proposal asks the
operator to reload rather than silently changing the reviewed quantities. The batch's
UUID filter stays out of the PO filter picker while its scope remains visible above the
list. These are application rules layered on VUEDA's action, metadata, form, and CRUD
surfaces, as described in the published
[action contract](https://vueda.dev/v3/core-concepts/action-contract-and-availability.html)
and [action form reference](https://vueda.dev/v3/reference/api/vue/ActionForm.html).
