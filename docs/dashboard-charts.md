# Dashboard charts

The dashboard combines native Unovis components with VUEDA's list adapter and
reactive-helpers. Chart panels load asynchronously, so routes without charts do not
load Unovis. Both panels require purchase-order list access. The server independently
checks that permission and applies row-level and workflow-state visibility before
aggregation.

## Reports and navigation

Both GET routes are mounted as the purchase-order viewset's `list` action. They reuse
its filterset and permission behavior without registering another model or inventing
chart-specific permissions:

- `/routes/catalog/purchaseorder/pipeline/` returns each workflow state, including
  zero-count states, with `id`, `code`, `name`, and `order_count`. IDs are state IDs.
  Rows follow workflow order. `columnTotals.order_count` is the sum of these counts.
- `/routes/catalog/purchaseorder/purchasing_trend/` returns each supplier with matching
  order lines, sorted by supplier slug. Rows contain `id` (supplier ID), `code` (slug),
  `name`, and `values`, an ascending array of `{week, value}`. `week` is an ISO Monday
  date and `value` is an exact decimal string. Each returned supplier has one observation
  for every week, including explicit zeroes. An empty report has `results: []`.

These are complete reports in VUEDA list envelopes: `results`, `totalRecords`,
`totalPages: 1`, `perPage`, and `columnTotals`. Pagination parameters do not slice the
report. The purchasing report accepts 1 to 26 complete Monday-to-Sunday weeks and
requires `purchasing=true`; it does not summarize a page of raw orders. Its result size
scales with the suppliers with matching lines, with at most 26 observations per supplier.

The pipeline defaults to the last 30 days, including today, and also offers 90 days
and all time. It shows the **current state of orders placed in the period**, not a
historical reconstruction of states. It reuses the existing database summary view's
state labels and ordering, replacing its all-time counts with authorized, filtered
counts. The original all-time summary endpoint remains available as a database-view
integration example.

Purchasing includes orders currently approved or received, using their `order_date`
and the sum of `quantity_ordered * unit_price`. Draft, submitted, and cancelled orders
are excluded. This is recorded purchasing value, not payments, revenue, or received-on
history. No currency is stored, so the UI does not invent a denomination.

Date fields have no time of day. Client period boundaries use the UTC calendar and
week starts are formatted in UTC, avoiding browser timezone shifts. The report and
history seed also calculate the current date in UTC. The purchasing chart excludes
the current incomplete week. Amounts use the viewer's locale; decimal strings become
numbers for plotting.

Pipeline links combine the requested date filters with `workflow_state`. Purchasing
links combine each week's inclusive date bounds, `purchasing=true`, and the supplier
ID. Both land on the same order list and filters used by the reports. Zero values do
not link. In particular, the workflow filter only accepts states that currently hold
orders, so an empty state must not produce an invalid link.

## Request lifecycle

`useList` owns managed rows, loading/errors, cancellation, and disposal. Each panel
uses `singlePagePaginatedListCrudAdaptor`, with the report name supplied as the target's
`action`. Reporting-period changes drive reactive request parameters. Refresh and Retry
use the same adapter; refresh also checks whether the UTC date has changed.

The adapter clears previous rows at the start of a request. Both panels show a skeleton
and derive no chart rows during loading; old values are never shown under new period
labels. The adapter checks cancellation before publishing results. Leaving the page
stops the list scope. Error messages include a retry button, and empty data is shown
explicitly. Supplier toggles filter the already-complete report locally without changing
the managed rows.

## Styling and category identity

Import `@vueda/theme/vueda-tailwind/unovis.css` from the VUEDA client package and apply
`unovis-vueda` to the chart scope. See the [VUEDA Unovis guide](https://vueda.dev/v3/guides/style-unovis-charts.html)
when the accompanying integration is released. There is no application-local copy of
the token mapping. This change requires the VUEDA client version containing that file;
it currently works with a contributor's linked package.

The five demo suppliers have explicit, stable color and dash assignments in
`client/src/charts/purchasing.js`. Filtering or reordering cannot renumber them. The
pipeline uses the palette's default blue, while controls and links keep the UI's primary
colors. The categorical palette is a light/dark Okabe-Ito derivative stored as OKLCH.
Additional supplier slugs receive a deterministic fallback slot; five colors are not
an unlimited categorical palette. For a larger supplier catalog, choose explicit
assignments and limit simultaneous series or use separate small charts.

The supplier buttons show matching line samples and expose `aria-pressed`. The data
table contains exact values and keyboard-accessible order links. Tooltip text is built
with DOM `textContent`; server-provided names are not inserted as HTML.

## Demo history

`seed_demo` adds 130 received orders: one per supplier per week for 26 complete
weeks. Quantities vary deterministically, with different supplier trends. Stable
`PO-HIST-<supplier>-<week>` references make reseeding idempotent. Dates roll forward
with the seed date, and existing workflow state changes survive. Historical fixtures do
not execute stock receipt actions or change current inventory quantities.

Use the normal seed workflow from the README. No model migration is needed for these
reports or history rows.
