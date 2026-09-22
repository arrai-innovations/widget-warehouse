# Integration examples

These are the VUEDA integration points behind the [demo walkthrough](../README.md#create-and-approve-a-replenishment-order).

## Permissions and navigation

`seed_demo_users` defines groups, model permissions, and the published accounts.
The inventory supervisor has update permission on inventory records, without create
or delete. This covers every writable field, including counts, targets, and relations.
Supplier permissions also cover the whole model: either inventory role can update its
approval flag as well as its contact details.

`client/src/TheNav.vue` builds navigation from each model's permitted actions in
VUEDA metadata. Dashboard tiles use the same permission information to decide which
models to query. No separate menu definition is maintained for each role.

See VUEDA's [permission model](https://vueda.dev/v3/core-concepts/permission-model.html)
and [row-level filtering](https://vueda.dev/v3/core-concepts/row-level-permission-filtering.html).

## Purchase order workflow

`server/widget_warehouse/catalog/management/commands/seed_workflows.py` defines the
workflow as data and attaches its permissions to the demo groups.

| Transition             | From                       | To        | Role                          |
| ---------------------- | -------------------------- | --------- | ----------------------------- |
| Submit for approval    | Draft                      | Submitted | Inventory clerk or supervisor |
| Approve                | Submitted                  | Approved  | Inventory supervisor          |
| Reject                 | Submitted                  | Draft     | Inventory supervisor          |
| Receive into warehouse | Approved                   | Received  | Inventory supervisor          |
| Cancel                 | Draft, Submitted, Approved | Cancelled | Inventory supervisor          |

Receiving changes only workflow state. It does not post inventory or implement partial
receipts. Received and cancelled orders are excluded from replenishment coverage.

Three permission layers apply:

- The workflow gate requires `read_purchaseorder`. The accountant can inspect the
  workflow but cannot execute any transition.
- Transition permissions grant specific decisions, such as `approve_purchaseorder`.
  The order must also be in a valid source state.
- State permissions deny the clerk's baseline update permission after Draft. Returning
  an order to Draft restores the clerk's update action.

The server tests in `server/tests/test_purchase_order_workflow.py` exercise these
rules through the API with the published roles.

## Forms, warnings, and totals

Purchase orders serialize their lines as a writable inline. In
`client/src/setupModelConfig.js`, create, read, and update views expand `lines`;
list views expand supplier and destination warehouse instead. Omitting an existing
line from an update deletes it.

`catalog/serializers.py` supplies advisory warnings for delivery dates shorter than
a supplier's lead time and stock counts above a location's maximum. The client uses
VUEDA's [warning confirmation dialog](https://vueda.dev/v3/reference/api/vue/#formconfirmdialog).
Cancelling leaves stored values unchanged; acknowledging the warning permits the save.

The purchase-order queryset annotates `total_value` from its lines. The serializer
reports the field's type with `get_field_model_info`, and the viewset totals it over
the filtered queryset. Inventory totals `quantity_on_hand` in the same way.

Supplier `notification_emails` uses the `FieldSetMany` override in
`client/src/setupModelConfig.js` to render multiple email inputs. Widget serializers
also expose file, image, duration, and JSON fields; promotions expose a date range.
The published roles browse widgets and promotions without updating them.

## Replenishment action and pricing

`InventoryRecordViewSet.replenish` provides GET preview and POST execution for selected
inventory records. `client/src/router/index.js` registers
`ViewActionCatalogInventoryrecordReplenish.vue` through `setCrudComponents`; that view
uses `useForm` and `ActionForm` with the standard list selection.

`catalog/replenishment.py` calculates coverage from on-hand stock, approved incoming
orders, and pending draft or submitted orders. It proposes enough to reach the maximum
stock level (or threshold when no maximum exists), but only when coverage is below
the reorder threshold. Orders are grouped by supplier and destination warehouse.

Execution checks the reviewed quantities again and creates the batch atomically.
An idempotent batch identifier prevents retries from duplicating orders. VUEDA's
`Dry-Run` header validates without creating orders or batch receipts. A stale proposal
requires another review. The resulting list is scoped to the batch, with a visible
control to return to all orders.

`catalog/pricing.py` and `client/src/use/usePurchasePriceDefaults.js` supply the default
price for a newly selected variant from the chosen supplier. Reselecting a variant or
changing supplier looks it up again. The API applies the same default when a new line
omits its price; an explicit price, including zero, takes precedence. Each saved order
line owns its price independently of later supplier-price changes.

See the published [action contract](https://vueda.dev/v3/core-concepts/action-contract-and-availability.html)
and [ActionForm reference](https://vueda.dev/v3/reference/api/vue/ActionForm.html).

## Dashboard

Tiles in `client/src/views/ViewDashboard.vue` request a single row and use
`totalRecords` for the filtered count. Each tile links to the same filtered list.
Open order value uses the order list's `columnTotals`.

The pipeline and supplier purchasing charts use native Unovis components with VUEDA's
optional theme stylesheet. [Dashboard charts](dashboard-charts.md) documents the report
contracts, request lifecycle, and styling.
