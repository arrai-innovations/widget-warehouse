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

All three are idempotent, so a deployed instance can be reseeded at any time. Reseeding
does not walk an order back: `seed_catalog` puts an order into its seeded workflow state
when it creates the order and not afterwards, and `seed_workflows` only gives a starting
state to orders that have none, which is what backfills orders seeded before the workflow
existed. `seed_demo_users` resets each demo password on every run, so the credentials on
the sign-in view always work.

The seeded orders are spread across the pipeline rather than all left in draft: three
drafts waiting to be submitted, two waiting for approval, three approved (two of them
already past their expected arrival), three received, and one cancelled. Some seeded stock
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

## Purchase Orders

A purchase order carries its lines as a writable inline, so one request creates or
updates the order and its line rows together. The client sends the `lines` expand on
create and update, which is what makes the nested payload deserialize as objects rather
than as ids; a line left out of an update is deleted. Sign in as the clerk and edit
`PO-1044`, one of the seeded drafts, to see it. The list view deliberately does not expand the lines: it shows the
supplier and destination warehouse instead.

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

Running a transition is a server capability today. The client surface for triggering one
is the next piece of work.
