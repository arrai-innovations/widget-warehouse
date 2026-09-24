"""
Contract tests for the view-backed order pipeline summary.

``PurchaseOrderStateCount`` is an unmanaged model over a database view, exposed through an
ordinary VUEDA serializer, viewset, and route. These cover the three things that make it
worth having: it answers in one request, it reports a state holding no orders as a zero
rather than refusing the question, and it is gated by ordinary model permissions.

The last test is the reason the view exists at all. Counting by filtering the order list
once per state cannot work, because the workflow state filter rejects a state no order is
in. See ``test_purchase_order_filters.py`` for that behaviour on its own.
"""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from vueda.workflow.models import State, Workflow

from widget_warehouse.catalog.models import (
    PurchaseOrder,
    PurchaseOrderStateCount,
    Supplier,
    Warehouse,
)
from widget_warehouse.catalog.seeding import DemoUsers, PurchaseOrderWorkflow

PIPELINE = ("draft", "submitted", "approved", "received", "cancelled")


@pytest.fixture
def orders(db):
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
    made = [
        PurchaseOrder.objects.create(
            reference=reference,
            supplier=supplier,
            destination_warehouse=warehouse,
            order_date=date(2026, 9, 1),
        )
        for reference in ("PO-1", "PO-2", "PO-3")
    ]

    # Two of the three leave draft, so the counts under test are not all the same number.
    workflow = Workflow.objects.get(content_type=PurchaseOrder.get_content_type())
    states = {state.code: state for state in State.objects.filter(workflow=workflow)}
    for order, code in zip(made[1:], ("submitted", "approved"), strict=True):
        state_row = order.object_state
        state_row.state = states[code]
        state_row.save()

    return made


def list_as(email, params=None):
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=email))
    return client.get(reverse("catalog.purchaseorderstatecount-list"), params or {})


@pytest.mark.django_db
def test_one_request_returns_every_state_in_pipeline_order(orders):
    response = list_as("clerk@widgetwarehouse.com")

    assert response.status_code == 200, response.data
    assert [row["code"] for row in response.data["results"]] == list(PIPELINE)


@pytest.mark.django_db
def test_a_state_holding_no_orders_is_a_zero_rather_than_a_refusal(orders):
    """
    The point of the view. Asking the order list for ``received`` would be a 400, because
    the workflow state filter only accepts states some row is in. Here it is a row.
    """
    response = list_as("clerk@widgetwarehouse.com")

    counts = {row["code"]: row["order_count"] for row in response.data["results"]}
    assert counts == {"draft": 1, "submitted": 1, "approved": 1, "received": 0, "cancelled": 0}


@pytest.mark.django_db
def test_the_totals_row_carries_the_order_count(orders):
    response = list_as("clerk@widgetwarehouse.com", {"ct": "order_count"})

    # column_totals sums over the whole filtered queryset, so this is every order that has
    # a state, for free, in the same request as the breakdown.
    assert response.data["columnTotals"] == {"order_count": 3}


@pytest.mark.django_db
def test_only_the_roles_that_read_orders_read_the_summary(orders):
    for email in ("clerk@widgetwarehouse.com", "supervisor@widgetwarehouse.com", "accountant@widgetwarehouse.com"):
        assert list_as(email).status_code == 200, email

    # The outbound roles cannot list purchase orders, so they cannot count them either.
    for email in ("associate@widgetwarehouse.com", "manager@widgetwarehouse.com"):
        assert list_as(email).status_code == 403, email


@pytest.mark.django_db
def test_the_summary_is_read_only_through_the_api(orders):
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email="supervisor@widgetwarehouse.com"))
    row = PurchaseOrderStateCount.objects.first()

    # No role is granted create, update, or delete on a model with nothing to write to, so
    # the API refuses before the database's own no-op rules are ever reached.
    assert client.post(reverse("catalog.purchaseorderstatecount-list"), {"code": "x"}, format="json").status_code == 403
    detail = reverse("catalog.purchaseorderstatecount-detail", kwargs={"pk": row.pk})
    assert client.patch(detail, {"order_count": 99}, format="json").status_code == 403
    assert client.delete(detail).status_code == 403


@pytest.mark.django_db
def test_a_state_row_left_behind_by_a_deleted_order_does_not_inflate_a_count(orders):
    """
    Object state is not a catalog table, so discarding orders does not discard their state
    rows; reset_demo clears them separately. The view joins the orders back, so a widowed
    state row counts nothing.
    """
    PurchaseOrder.objects.filter(reference="PO-2").delete()

    counts = {row["code"]: row["order_count"] for row in list_as("clerk@widgetwarehouse.com").data["results"]}
    assert counts["submitted"] == 0
