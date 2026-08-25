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
just manage seed_catalog
just manage seed_demo_users
```

Both commands are idempotent, so a deployed instance can be reseeded at any time.
`seed_demo_users` resets each demo password on every run, so the credentials on the
sign-in view always work.

## Demo Roles

Five groups and one user per group are seeded as data by `seed_demo_users`, not as
fixtures and not through the DEBUG-only permission overview UI, so the whole matrix
reproduces on deploy. Every account uses the password `widget-demo`, and the sign-in
view lists them so an evaluator can switch roles without leaving the page.

| Group                  | Sign in as                     | Reads                                                 | Writes                       | Transitions                              |
| ---------------------- | ------------------------------ | ----------------------------------------------------- | ---------------------------- | ---------------------------------------- |
| `inventory-clerk`      | clerk@widgetwarehouse.com      | catalog, inventory, suppliers, warehouses             | purchase order drafts        | `submit`                                 |
| `inventory-supervisor` | supervisor@widgetwarehouse.com | catalog, inventory, suppliers, warehouses             | purchase orders in any state | `submit`, `approve`, `reject`, `receive` |
| `sales-associate`      | associate@widgetwarehouse.com  | catalog, inventory, warehouses, promotions, customers | sales order drafts           | `submit`                                 |
| `sales-manager`        | manager@widgetwarehouse.com    | catalog, inventory, warehouses, promotions, customers | sales orders in any state    | `submit`, `approve`, `reject`, `ship`    |
| `accountant`           | accountant@widgetwarehouse.com | everything                                            | nothing                      | none, plus a bulk export action          |

Customers, purchase orders, and sales orders are not modelled yet. Each role grants
what the table says for every model that does exist, which leaves all five read-only for
now, and leaves the two inventory roles granting the same access as each other, as do
the two sales roles.

What is live today is the Reads column. Sign in as the clerk and the sales associate in
turn: both get the same widgets, categories, variants, inventory records, and
warehouses, but only the clerk sees Suppliers and only the associate sees Promotions.
The navigation is not built per role in client code. It asks VUEDA for each model's
metadata, and VUEDA reports only the actions the signed-in user is permitted, so the
menu, the row actions, and the API all answer from one permission decision. Sign in as
the superuser to see the same screens with create, update, and delete restored.
