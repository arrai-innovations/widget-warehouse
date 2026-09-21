"""
Shape tests for the seeded demo data.

Widget Warehouse is deployed as a public demo whose credentials are printed on the sign-in
form, so it resets on a schedule and the seed is the demo: a number the seed cannot produce
is a number no evaluator ever sees. These pin the shapes that are decisions rather than
details, which is everything the landing page counts and the walkthrough walks.

The seed is deliberately deterministic, so the counts below are exact. A change to the
quantities or the state column should land here too, with the new number, rather than be
absorbed by an assertion loose enough not to notice.
"""

from datetime import date

import pytest
from django.core.management import call_command
from django.db.models import F, Q
from vueda.workflow.models import State

from widget_warehouse.catalog.models import (
    InventoryRecord,
    PurchaseOrder,
    PurchaseOrderStateCount,
    Widget,
    WidgetVariant,
)

# The spread the pipeline band on the landing page renders. Three drafts is the
# walkthrough's supply: an evaluator submits one and there are still drafts behind it.
SEEDED_PIPELINE = {"draft": 3, "submitted": 2, "approved": 3, "received": 133, "cancelled": 1}

# Rows under their own reorder threshold, which is what the restock queue counts.
SEEDED_RESTOCK_ROWS = 15


@pytest.fixture
def seeded(db):
    call_command("seed_demo_users", verbosity=0)
    call_command("seed_workflows", verbosity=0)
    call_command("seed_catalog", verbosity=0)


def pipeline():
    return {row.code: row.order_count for row in PurchaseOrderStateCount.objects.all()}


def below_reorder():
    return InventoryRecord.objects.filter(quantity_on_hand__lt=F("reorder_threshold"))


def test_orders_are_spread_across_the_pipeline(seeded):
    assert pipeline() == SEEDED_PIPELINE
    assert PurchaseOrder.objects.count() == sum(SEEDED_PIPELINE.values())


def test_the_supervisor_has_overdue_orders_to_notice(seeded):
    """
    An order is overdue when it is still in flight and its expected arrival has passed.
    A received order with a date in the past arrived; it is not late.
    """
    overdue = PurchaseOrder.objects.filter(
        expected_arrival_date__lt=date.today(),
        object_states_proxy__state__code__in=("submitted", "approved"),
    )

    assert overdue.count() == 2


def test_the_restock_queue_is_not_empty(seeded):
    assert below_reorder().count() == SEEDED_RESTOCK_ROWS

    # In both stocked warehouses, so the queue is a real list to filter rather than one
    # warehouse's problem.
    assert below_reorder().values("warehouse__code").distinct().count() == 2


def test_the_seed_carries_the_boundary_the_restock_filter_turns_on(seeded):
    """
    Equal to the threshold is not below it. The Melbourne row for the medium sprocket is
    seeded at exactly its threshold so the demo data itself holds the case, and a filter
    that started using ``lte`` would fail here rather than quietly overcount.
    """
    boundary = InventoryRecord.objects.get(variant__sku_suffix="MD", warehouse__code="MEL-OVF")

    assert boundary.quantity_on_hand == boundary.reorder_threshold
    assert boundary not in below_reorder()


def test_the_bulk_catalog_has_variants_to_hang_stock_off(seeded):
    """
    Inventory points at a variant, not a widget, so a widget with no variant can hold no
    stock. Before the bulk widgets had one, the stock levels described five widgets out of
    sixty-three.
    """
    widgets_without_variants = Widget.objects.filter(variants__isnull=True).count()
    variants_without_stock = WidgetVariant.objects.filter(inventory__isnull=True).count()

    assert widgets_without_variants < Widget.objects.count() / 4
    assert variants_without_stock == 0


def test_reseeding_leaves_an_advanced_order_where_an_evaluator_left_it(seeded):
    """
    The seed sets an order's state when it creates the order and not afterwards, which is
    the same promise ``seed_workflows`` makes about its backfill. A deployed instance
    reseeds without undoing anybody's walkthrough; ``reset_demo`` is the undo half.
    """
    object_state = PurchaseOrder.objects.get(reference="PO-1043").object_state
    object_state.state = State.objects.get(workflow=object_state.workflow, code="submitted")
    object_state.save()

    call_command("seed_catalog", verbosity=0)

    assert PurchaseOrder.objects.get(reference="PO-1043").workflow_state.code == "submitted"


def test_reseeding_adds_nothing_and_changes_no_count(seeded):
    before = (
        Widget.objects.count(),
        WidgetVariant.objects.count(),
        InventoryRecord.objects.count(),
        PurchaseOrder.objects.count(),
        below_reorder().count(),
    )

    call_command("seed_catalog", verbosity=0)

    after = (
        Widget.objects.count(),
        WidgetVariant.objects.count(),
        InventoryRecord.objects.count(),
        PurchaseOrder.objects.count(),
        below_reorder().count(),
    )
    assert after == before
    assert pipeline() == SEEDED_PIPELINE


def test_seeding_the_catalog_before_the_workflow_still_produces_orders(db):
    """
    The documented run order is users, workflow, catalog. Out of order the orders land
    without the spread rather than failing, and ``seed_workflows`` backfills them into the
    initial state, which is what it exists for.
    """
    call_command("seed_catalog", verbosity=0)
    assert PurchaseOrder.objects.count() == sum(SEEDED_PIPELINE.values())

    call_command("seed_demo_users", verbosity=0)
    call_command("seed_workflows", verbosity=0)

    assert pipeline() == {
        "draft": PurchaseOrder.objects.count(),
        "submitted": 0,
        "approved": 0,
        "received": 0,
        "cancelled": 0,
    }


def test_every_seeded_order_has_lines_to_value(seeded):
    assert not PurchaseOrder.objects.filter(lines__isnull=True).exists()
    assert PurchaseOrder.objects.filter(Q(lines__quantity_ordered__lte=0)).count() == 0
