"""
Filter contract tests for the purchase order list.

``workflow_state`` comes from VUEDA's ``HasWorkflowFilterSetMixin`` rather than from this
project's filterset body, so these cover what the mixin actually does on this model: the
filter narrows by state, and its accepted values are the states the queryset currently
holds rather than the states the workflow defines. The second half is a framework
behaviour a dashboard has to design around, so it is pinned here rather than discovered
again later.
"""

from datetime import date

import pytest
from django.core.management import call_command
from vueda.workflow.models import State, Workflow

from widget_warehouse.catalog.filtersets import PurchaseOrderFilterSet
from widget_warehouse.catalog.models import PurchaseOrder, Supplier, Warehouse


@pytest.fixture
def orders(db):
    # seed_workflows looks the demo groups up by name for its state permissions, so the
    # roles have to exist first.
    call_command("seed_demo_users", verbosity=0)
    call_command("seed_workflows", verbosity=0)
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
def test_a_state_no_order_is_in_is_rejected_rather_than_returning_nothing(orders):
    """
    The mixin replaces the filter's queryset with the states present on the rows it was
    given (``vueda/server/vueda/workflow/filtersets.py:26``), and a ModelChoiceFilter
    validates against that same queryset. So asking for a state that currently holds no
    orders is an invalid choice, not an empty result. Anything counting orders per state
    has to handle a 400 where it expected a zero.
    """
    states = states_for_orders()
    assert not PurchaseOrder.objects.filter(object_states_proxy__state=states["approved"]).exists()

    filtered = PurchaseOrderFilterSet(
        {"workflow_state": str(states["approved"].pk)},
        queryset=PurchaseOrder.objects.all(),
    )

    assert not filtered.is_valid()
    assert "workflow_state" in filtered.errors


@pytest.mark.django_db
def test_an_empty_queryset_accepts_every_state_in_the_table(orders):
    """
    The narrowing is skipped when no row has a state at all, so the filter is at its most
    permissive with no data and at its strictest with data. States belonging to other
    workflows entirely become acceptable values here.
    """
    accepted = PurchaseOrderFilterSet(queryset=PurchaseOrder.objects.none()).filters["workflow_state"].queryset

    assert accepted.count() == State.objects.count()
