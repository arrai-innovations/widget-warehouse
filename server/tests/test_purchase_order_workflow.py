"""
Behaviour tests for the purchase order workflow's three permission layers.

These are the claims the walkthrough script makes, checked against the API an evaluator
would drive: an order starts in draft, the transitions a role is offered depend on both
the role and the row's current state, and submitting an order takes the edit away from
the clerk who raised it while leaving it with the supervisor.

The workflow itself is checked through ``seed_workflows`` rather than through fixtures
built here, so what these tests exercise is the definition a deployed instance runs.
"""

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from widget_warehouse.catalog.models import PurchaseOrder, Supplier, Warehouse

CLERK = "clerk@widgetwarehouse.com"
SUPERVISOR = "supervisor@widgetwarehouse.com"
ASSOCIATE = "associate@widgetwarehouse.com"
ACCOUNTANT = "accountant@widgetwarehouse.com"

WORKFLOW_KWARGS = {"app_label": "catalog", "model": "purchaseorder"}


@pytest.fixture
def order(db):
    call_command("seed_demo_users", verbosity=0)
    call_command("seed_workflows", verbosity=0)

    return PurchaseOrder.objects.create(
        reference="PO-2001",
        supplier=Supplier.objects.create(
            name="Precision Parts Co.",
            slug="precision-parts-co",
            contact_email="sales@example.com",
        ),
        destination_warehouse=Warehouse.objects.create(
            name="Sydney Distribution Centre",
            code="SYD-DC",
            address="42 Industrial Drive",
            opens_at="07:00",
            closes_at="18:00",
        ),
        order_date=date(2026, 9, 1),
        expected_arrival_date=date(2026, 9, 1) + timedelta(days=14),
    )


def client_for(email):
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=email))
    return client


def transitions_offered(email, order):
    """The transitions this role may run on this order right now."""
    response = client_for(email).get(
        reverse("workflow.workflow-object-transitions", kwargs={**WORKFLOW_KWARGS, "object_id": order.id})
    )
    assert response.status_code == 200, response.data
    return sorted(transition["code"] for transition in response.data)


def run_transition(email, order, code):
    return client_for(email).patch(
        reverse("workflow.workflow-execute-transition", kwargs={**WORKFLOW_KWARGS, "object_id": order.id}),
        {"transition_code": code},
        format="json",
    )


def state_of(order):
    order.refresh_from_db()
    return order.workflow_state.code


@pytest.mark.django_db
def test_a_new_order_starts_in_draft(order):
    """
    The state row is created by the model mixin's save, not by anything the seed does, so
    an order raised through the API is in the workflow from the moment it exists.
    """
    assert state_of(order) == "draft"


@pytest.mark.django_db
def test_the_order_reports_its_state_and_the_readers_transitions(order):
    response = client_for(CLERK).get(reverse("catalog.purchaseorder-detail", args=[order.id]))

    assert response.status_code == 200, response.data
    assert response.data["workflow_state_code"] == "draft"
    assert response.data["workflow_state_name"] == "Draft"
    # Carried on the row itself, so a list response has the state to show and the actions
    # to offer without a second request per row.
    assert [transition["code"] for transition in response.data["valid_transitions"]] == ["submit"]


@pytest.mark.django_db
def test_transitions_offered_depend_on_the_role_and_the_state(order):
    # Both inventory roles may submit a draft. Approve is a supervisor permission, but it
    # is offered to nobody yet because no transition leaves draft for it.
    assert transitions_offered(CLERK, order) == ["submit"]
    assert transitions_offered(SUPERVISOR, order) == ["cancel", "submit"]

    assert run_transition(CLERK, order, "submit").status_code == 200
    assert state_of(order) == "submitted"

    # The same two roles, the same order, one state later: the clerk has run out of
    # transitions and the supervisor picks up the approval decision.
    assert transitions_offered(CLERK, order) == []
    assert transitions_offered(SUPERVISOR, order) == ["approve", "cancel", "reject"]


@pytest.mark.django_db
def test_submitting_takes_the_edit_away_from_the_clerk_who_raised_it(order):
    """
    The walkthrough's state permission moment. The clerk's baseline permission grants
    update on any purchase order; the deny rule on the submitted state takes it back for
    this row, so the same user at the same URL loses the edit the moment they submit.
    """
    clerk = client_for(CLERK)
    detail_url = reverse("catalog.purchaseorder-detail", args=[order.id])

    assert clerk.patch(detail_url, {"reference": "PO-2001-A"}, format="json").status_code == 200

    assert run_transition(CLERK, order, "submit").status_code == 200

    denied = clerk.patch(detail_url, {"reference": "PO-2001-B"}, format="json")
    assert denied.status_code == 403, denied.data
    # Still readable. Only the write is taken away.
    assert clerk.get(detail_url).status_code == 200


@pytest.mark.django_db
def test_the_supervisor_still_edits_a_submitted_order(order):
    """The deny rule names one group, so it narrows the clerk without narrowing the role above them."""
    assert run_transition(CLERK, order, "submit").status_code == 200

    response = client_for(SUPERVISOR).patch(
        reverse("catalog.purchaseorder-detail", args=[order.id]),
        {"reference": "PO-2001-C"},
        format="json",
    )

    assert response.status_code == 200, response.data


@pytest.mark.django_db
def test_the_clerk_cannot_approve_their_own_submitted_order(order):
    assert run_transition(CLERK, order, "submit").status_code == 200

    denied = run_transition(CLERK, order, "approve")

    # Transition failures come back as validation errors, not as an authorization status.
    assert denied.status_code == 400, denied.data
    assert state_of(order) == "submitted"


@pytest.mark.django_db
def test_a_transition_is_refused_from_a_state_it_does_not_start_from(order):
    """Approve leaves submitted only, so the supervisor cannot approve a draft order."""
    denied = run_transition(SUPERVISOR, order, "approve")

    assert denied.status_code == 400, denied.data
    assert state_of(order) == "draft"


@pytest.mark.django_db
def test_the_supervisor_walks_an_order_to_received(order):
    assert run_transition(CLERK, order, "submit").status_code == 200
    assert run_transition(SUPERVISOR, order, "approve").status_code == 200
    assert run_transition(SUPERVISOR, order, "receive").status_code == 200

    assert state_of(order) == "received"
    # Received is the end of the line: nothing leaves it, for anyone.
    assert transitions_offered(SUPERVISOR, order) == []


@pytest.mark.django_db
def test_rejecting_returns_the_order_to_the_clerk(order):
    assert run_transition(CLERK, order, "submit").status_code == 200
    assert run_transition(SUPERVISOR, order, "reject").status_code == 200

    assert state_of(order) == "draft"
    # Back in draft, so the deny no longer applies and the clerk can edit and resubmit.
    edit = client_for(CLERK).patch(
        reverse("catalog.purchaseorder-detail", args=[order.id]),
        {"reference": "PO-2001-D"},
        format="json",
    )
    assert edit.status_code == 200, edit.data
    assert transitions_offered(CLERK, order) == ["submit"]


@pytest.mark.django_db
def test_the_accountant_reads_orders_but_is_offered_no_transitions(order):
    """
    The workflow gate is purchase order read, so the accountant sees the machinery; no
    transition permission matches, so the list of what they may run comes back empty.
    """
    assert client_for(ACCOUNTANT).get(reverse("catalog.purchaseorder-detail", args=[order.id])).status_code == 200
    assert transitions_offered(ACCOUNTANT, order) == []


@pytest.mark.django_db
def test_a_role_outside_the_workflow_reaches_no_purchase_order_at_all(order):
    """
    Regression guard for the deferral narrowed in PurchaseOrderViewSet. Left as the
    framework mixin has it, the presence of any state permission row defers the
    model-level check for every caller, and this role reads the whole list and can create
    orders despite holding no purchase order permission.
    """
    associate = client_for(ASSOCIATE)

    assert associate.get(reverse("catalog.purchaseorder-list")).status_code == 403
    assert associate.get(reverse("catalog.purchaseorder-detail", args=[order.id])).status_code == 403

    created = associate.post(
        reverse("catalog.purchaseorder-list"),
        {
            "reference": "PO-9999",
            "supplier": order.supplier_id,
            "destination_warehouse": order.destination_warehouse_id,
            "order_date": str(date(2026, 9, 1)),
        },
        format="json",
    )
    assert created.status_code == 403, created.data
    assert PurchaseOrder.objects.count() == 1


@pytest.mark.django_db
def test_reseeding_the_workflow_leaves_an_order_where_it_was(order):
    """
    A deployed instance reseeds, and reseeding must not walk orders back to draft. The
    backfill only touches orders with no state row at all.
    """
    assert run_transition(CLERK, order, "submit").status_code == 200

    call_command("seed_workflows", verbosity=0)

    assert state_of(order) == "submitted"
