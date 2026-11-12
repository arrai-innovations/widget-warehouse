"""
Filter contract tests for the purchase order list.

``workflow_state`` comes from VUEDA, which adds it to every filterset of a workflow model,
rather than from this project's filterset body. These cover what it does on this model: the
filter narrows by state, accepts any state the purchase order workflow defines whether or
not an order is in it, and rejects a state from another model's workflow.
"""

from datetime import date

import pytest
from django.contrib.contenttypes.models import ContentType
from vueda.workflow.models import State, Workflow

from widget_warehouse.catalog.filtersets import PurchaseOrderFilterSet
from widget_warehouse.catalog.models import PurchaseOrder, Supplier, Warehouse, Widget
from widget_warehouse.catalog.seeding import DemoUsers, PurchaseOrderWorkflow


@pytest.fixture
def orders(db):
    # The workflow step looks the demo groups up by name for its state permissions, so the
    # roles have to exist first.
    DemoUsers().run()
    PurchaseOrderWorkflow().run()
    supplier = Supplier.objects.create(
        name="Precision Parts Co.",
        slug="precision-parts-co",
        contact_email="sales@example.com",
    )
    warehouse = Warehouse.objects.create(
        name="Sydney Distribution Centre",
        code="SYD-DC",
        address="42 Industrial Drive",
        opens_at="07:00",
        closes_at="18:00",
    )
    made = []
    for reference in ("PO-1", "PO-2"):
        made.append(
            PurchaseOrder.objects.create(
                reference=reference,
                supplier=supplier,
                destination_warehouse=warehouse,
                order_date=date(2026, 9, 1),
            )
        )
    return made


def states_for_orders():
    workflow = Workflow.objects.get(content_type=PurchaseOrder.get_content_type())
    return {state.code: state for state in State.objects.filter(workflow=workflow)}


@pytest.mark.django_db
def test_workflow_state_filters_the_order_list(orders):
    states = states_for_orders()
    moved, stayed = orders
    # ``object_state`` re-queries on every access, so the row has to be held before it is
    # changed; assigning through the property twice would write to a discarded instance.
    state_row = moved.object_state
    state_row.state = states["submitted"]
    state_row.save()

    filtered = PurchaseOrderFilterSet(
        {"workflow_state": str(states["submitted"].pk)},
        queryset=PurchaseOrder.objects.all(),
    )

    assert filtered.is_valid(), filtered.errors
    assert list(filtered.qs.values_list("reference", flat=True)) == [moved.reference]
    assert stayed.reference not in list(filtered.qs.values_list("reference", flat=True))


@pytest.mark.django_db
def test_a_state_no_order_is_in_matches_no_orders(orders):
    """
    A state that currently holds no orders is a valid value with an empty result, so a
    saved list URL that names a state keeps working after the last order leaves it.
    """
    states = states_for_orders()
    assert not PurchaseOrder.objects.filter(object_states_proxy__state=states["approved"]).exists()

    filtered = PurchaseOrderFilterSet(
        {"workflow_state": str(states["approved"].pk)},
        queryset=PurchaseOrder.objects.all(),
    )

    assert filtered.is_valid(), filtered.errors
    assert not filtered.qs.exists()


@pytest.mark.django_db
def test_a_state_from_another_workflow_is_rejected(orders):
    content_type = ContentType.objects.get_for_model(Widget)
    other = Workflow.objects.create(
        code="widget-review",
        name="Widget review",
        content_type=content_type,
        historical_app_label=content_type.app_label,
        historical_model=content_type.model,
    )
    foreign_state = State.objects.create(workflow=other, code="draft", name="Draft")

    filtered = PurchaseOrderFilterSet(
        {"workflow_state": str(foreign_state.pk)},
        queryset=PurchaseOrder.objects.all(),
    )

    assert not filtered.is_valid()
    assert "workflow_state" in filtered.errors
