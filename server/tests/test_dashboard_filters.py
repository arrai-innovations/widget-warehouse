"""
Contract tests for the four filters the dashboard's work queues count with.

Each tile on the landing page is a list request narrowed by a filter, so a tile is only as
honest as the filter behind it. These four are the ones the generated filters could not
express: a three-state boolean asked for its undecided state, a containment test against a
range column, and two questions that read the workflow state, one of them alongside a date
column.

The counts themselves come from the paginated envelope's ``totalRecords``, so the tests
read it the same way a tile does rather than counting rows on the page.
"""

import json
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from psycopg.types.range import Range
from rest_framework.test import APIClient
from vueda.workflow.models import ObjectState

from widget_warehouse.catalog.models import Promotion, PurchaseOrder, Supplier, Warehouse

CLERK = "clerk@widgetwarehouse.com"
# Promotions belong to the sales roles: the clerk cannot list them at all, which is the
# same split the dashboard's promotion tile relies on to disappear for the wrong role.
ASSOCIATE = "associate@widgetwarehouse.com"
SUPERVISOR = "supervisor@widgetwarehouse.com"


@pytest.fixture
def suppliers(db):
    call_command("seed_demo_users", verbosity=0)
    for slug, approved in (
        ("approved-one", True),
        ("approved-two", True),
        ("rejected", False),
        ("waiting", None),
        ("also-waiting", None),
    ):
        Supplier.objects.create(
            name=slug.replace("-", " ").title(),
            slug=slug,
            contact_email=f"{slug}@example.com",
            is_approved=approved,
        )


@pytest.fixture
def promotions(db):
    call_command("seed_demo_users", verbosity=0)
    for code, lower, upper in (
        ("RUNNING", date(2026, 9, 1), date(2026, 10, 1)),
        ("ALSO-RUNNING", date(2026, 9, 15), date(2026, 9, 20)),
        ("OVER", date(2026, 8, 1), date(2026, 9, 1)),
        ("NOT-YET", date(2026, 10, 1), date(2026, 11, 1)),
    ):
        Promotion.objects.create(
            name=code.title(),
            code=code,
            discount_percent="10.00",
            valid_dates=Range(lower, upper),
        )


def list_as(email, route, params):
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=email))
    return client.get(reverse(route), params)


def test_under_review_counts_only_the_undecided_suppliers(suppliers):
    response = list_as(CLERK, "catalog.supplier-list", {"under_review": "true"})

    assert response.status_code == 200, response.data
    assert response.data["totalRecords"] == 2
    assert {row["slug"] for row in response.data["results"]} == {"waiting", "also-waiting"}


def test_under_review_false_is_every_supplier_that_has_been_decided(suppliers):
    """
    The complement, not "everything". A rejected supplier is decided, so it belongs with
    the approved ones rather than in the review queue.
    """
    response = list_as(CLERK, "catalog.supplier-list", {"under_review": "false"})

    assert response.data["totalRecords"] == 3
    assert {row["slug"] for row in response.data["results"]} == {"approved-one", "approved-two", "rejected"}


def test_the_generated_approval_filter_still_asks_its_own_question(suppliers):
    """
    ``under_review`` is added beside ``is_approved`` rather than replacing it, so a list
    can still be narrowed to the rejected suppliers alone.
    """
    response = list_as(CLERK, "catalog.supplier-list", {"is_approved": "false"})

    assert response.data["totalRecords"] == 1
    assert response.data["results"][0]["slug"] == "rejected"


def test_active_on_finds_the_promotions_running_that_day(promotions):
    response = list_as(ASSOCIATE, "catalog.promotion-list", {"active_on": "2026-09-18"})

    assert response.status_code == 200, response.data
    assert response.data["totalRecords"] == 2
    assert {row["code"] for row in response.data["results"]} == {"RUNNING", "ALSO-RUNNING"}


def test_active_on_respects_the_range_bounds_rather_than_guessing_them(promotions):
    """
    A Django ``DateRangeField`` stores a half-open range, so the upper bound is the first
    day the promotion is no longer running. ``__contains`` answers with the range's own
    bounds, which a pair of hand-written date comparisons would have to get right by hand.
    """
    starts = list_as(ASSOCIATE, "catalog.promotion-list", {"active_on": "2026-09-01"})
    ends = list_as(ASSOCIATE, "catalog.promotion-list", {"active_on": "2026-10-01"})

    # The 1st of September: RUNNING has started, OVER has ended.
    assert {row["code"] for row in starts.data["results"]} == {"RUNNING"}
    # The 1st of October: RUNNING has ended, NOT-YET has started.
    assert {row["code"] for row in ends.data["results"]} == {"NOT-YET"}


def test_both_filters_are_offered_to_the_client_as_ordinary_filters(promotions, suppliers):
    """
    A declared filter is reported in model info like a generated one, which is what lets
    the list view render it without knowing either is special.
    """
    client = APIClient()
    for model, expected, email in (
        ("supplier", "under_review", CLERK),
        ("promotion", "active_on", ASSOCIATE),
    ):
        client.force_authenticate(get_user_model().objects.get(email=email))
        url = reverse("info.model_info-detail", kwargs={"app_label": "catalog", "model": model})
        response = client.get(f"{url}?f=model_filtering&e=model_filtering")

        assert response.status_code == 200, response.data
        assert expected in response.data["model_filtering"], model


@pytest.fixture
def orders(db):
    call_command("seed_demo_users", verbosity=0)
    call_command("seed_workflows", verbosity=0)
    call_command("seed_catalog", verbosity=0)


def test_overdue_skips_an_order_that_already_arrived(orders):
    """
    The reason this filter exists. A received order's expected arrival is in the past too,
    and a date comparison on its own would report every historical order as late.
    """
    response = list_as(SUPERVISOR, "catalog.purchaseorder-list", {"overdue": "true"})

    assert response.status_code == 200, response.data
    references = {row["reference"] for row in response.data["results"]}
    assert references == {"PO-1041", "PO-1048"}

    settled = list_as(SUPERVISOR, "catalog.purchaseorder-list", {"expected_arrival_date_before": date.today()})
    # Five orders have a date in the past; three of them are done with.
    assert settled.data["totalRecords"] == 5


def test_overdue_false_is_every_order_nobody_is_waiting_on(orders):
    total = list_as(SUPERVISOR, "catalog.purchaseorder-list", {}).data["totalRecords"]
    overdue = list_as(SUPERVISOR, "catalog.purchaseorder-list", {"overdue": "true"}).data["totalRecords"]

    response = list_as(SUPERVISOR, "catalog.purchaseorder-list", {"overdue": "false"})

    assert response.data["totalRecords"] == total - overdue


def test_overdue_ignores_an_order_with_no_expected_arrival_at_all(orders):
    """
    A null arrival date is not late, it is unscheduled. PO-1044 is a seeded draft with no
    date, so it belongs in neither answer's overdue half.
    """
    overdue = list_as(SUPERVISOR, "catalog.purchaseorder-list", {"overdue": "true"})
    not_overdue = list_as(SUPERVISOR, "catalog.purchaseorder-list", {"overdue": "false"})

    assert "PO-1044" not in {row["reference"] for row in overdue.data["results"]}
    assert "PO-1044" in {row["reference"] for row in not_overdue.data["results"]}


def test_open_covers_everything_that_has_not_settled(orders):
    """
    Defined by what it excludes, so a state added to the workflow counts as open until
    somebody says otherwise. Against the seeded pipeline that is the drafts, the submitted,
    and the approved: eight of twelve.
    """
    response = list_as(SUPERVISOR, "catalog.purchaseorder-list", {"is_open": "true"})

    assert response.status_code == 200, response.data
    assert response.data["totalRecords"] == 8


def test_open_and_settled_are_complements(orders):
    total = list_as(SUPERVISOR, "catalog.purchaseorder-list", {}).data["totalRecords"]
    settled = list_as(SUPERVISOR, "catalog.purchaseorder-list", {"is_open": "false"})

    assert settled.data["totalRecords"] == total - 8
    # Received and cancelled, which is the whole of "settled".
    assert settled.data["totalRecords"] == 4


def test_an_order_with_no_workflow_state_counts_as_open(orders):
    """
    A row that predates the workflow is not a finished order. This is reachable in a
    deployment: seed_catalog run before seed_workflows leaves orders stateless until the
    backfill, and the value tile should not quietly drop them in the meantime.
    """
    stateless = PurchaseOrder.objects.create(
        reference="PO-NOSTATE",
        supplier=Supplier.objects.first(),
        destination_warehouse=Warehouse.objects.first(),
        order_date=date.today(),
    )
    ObjectState.objects.filter(object_id=stateless.id, workflow__code="purchase-order").delete()
    assert stateless.workflow_state is None

    response = list_as(SUPERVISOR, "catalog.purchaseorder-list", {"is_open": "true"})

    assert "PO-NOSTATE" in {row["reference"] for row in response.data["results"]}


def test_the_open_value_reaches_the_client_as_a_number_it_can_render(orders):
    """
    The value tile reads ``columnTotals`` rather than ``totalRecords``, so what matters is
    the rendered JSON rather than the Python object behind it. DRF encodes a Decimal as a
    JSON number, while the per-row field is a string, so the tile formats a number and the
    column formats a string. Pinned here because the tile would silently render
    "undefined" if either shape changed.
    """
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=SUPERVISOR))

    response = client.get(reverse("catalog.purchaseorder-list"), {"is_open": "true", "ps": 1})
    payload = json.loads(response.content)

    assert isinstance(payload["columnTotals"]["total_value"], (int, float))
    assert payload["columnTotals"]["total_value"] > 0
    assert isinstance(payload["results"][0]["total_value"], str)


def test_a_total_over_no_rows_is_null_rather_than_zero(orders):
    """
    ``Sum`` over an empty queryset returns NULL, which the annotation's own Coalesce does
    not reach: that one fills in a row with no lines, not a page with no rows. The tile has
    to read null as nothing rather than render it.
    """
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=SUPERVISOR))

    response = client.get(reverse("catalog.purchaseorder-list"), {"reference": "no-such-order"})
    payload = json.loads(response.content)

    assert payload["totalRecords"] == 0
    assert payload["columnTotals"] == {"total_value": None}
