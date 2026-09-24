"""
What the landing page adds up to, per role, against the seeded demo data.

The dashboard's claim is that one page with no per-role branching shows a different set of
work to each signed-in role, because the server decides. The page asks two questions per
tile: may this account list the model (from model info), and how many rows match (from the
list envelope's ``totalRecords``). Both are server answers, so both are testable here
without mounting the page, which is the only part of the claim a component test would add.

The tile declarations live in ``client/src/views/ViewDashboard.vue``. These mirror them. A
tile added there without a line here is a number nobody has checked.
"""

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

CLERK = "clerk@widgetwarehouse.com"
SUPERVISOR = "supervisor@widgetwarehouse.com"
ACCOUNTANT = "accountant@widgetwarehouse.com"
ASSOCIATE = "associate@widgetwarehouse.com"
MANAGER = "manager@widgetwarehouse.com"

INBOUND_ROLES = (CLERK, SUPERVISOR)
SALES_ROLES = (ASSOCIATE, MANAGER)

# The work queues, as the page declares them: a model and the filter that narrows it.
QUEUE_TILES = {
    "restock": ("inventoryrecord", {"below_reorder": "true"}),
    "overdue": ("purchaseorder", {"overdue": "true"}),
    "review": ("supplier", {"under_review": "true"}),
    "promotions": ("promotion", {"active_on": "today"}),
    "open-value": ("purchaseorder", {"is_open": "true"}),
}

# The scale numbers, which take no filter.
SCALE_TILES = {
    "widgets": "widget",
    "variants": "widgetvariant",
    "suppliers": "supplier",
    "warehouses": "warehouse",
    "orders": "purchaseorder",
}


@pytest.fixture
def demo(db):
    call_command("seed_demo", verbosity=0)


def client_for(email):
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=email))
    return client


def may_list(client, model):
    """The question the page asks before it renders a tile at all."""
    url = reverse("info.model_info-detail", kwargs={"app_label": "catalog", "model": model})
    response = client.get(f"{url}?f=model_actions&e=model_actions")
    assert response.status_code == 200, response.data
    return any(action["name"] == "list" for action in response.data["model_actions"])


def count(client, model, params=None):
    """The question the page asks next: one row, and read the envelope."""
    response = client.get(reverse(f"catalog.{model}-list"), {**(params or {}), "ps": 1})
    assert response.status_code == 200, response.data
    return response.data["totalRecords"]


def visible_queues(email):
    client = client_for(email)
    return {key for key, (model, _) in QUEUE_TILES.items() if may_list(client, model)}


@pytest.mark.parametrize("email", INBOUND_ROLES)
def test_the_inbound_roles_get_the_stock_and_order_queues_but_not_promotions(demo, email):
    assert visible_queues(email) == {"restock", "overdue", "review", "open-value"}


@pytest.mark.parametrize("email", SALES_ROLES)
def test_the_sales_roles_get_the_stock_and_promotion_queues_and_nothing_inbound(demo, email):
    """
    The same page, the same tile declarations, a different page. Orders and suppliers are
    not hidden by a rule on this page: model info reports no list action for them, so the
    tiles resolve to nothing and are never rendered.
    """
    assert visible_queues(email) == {"restock", "promotions"}


def test_the_accountant_reads_every_queue(demo):
    """
    The role that reads everything and writes nothing sees the full set. The tiles are the
    same tiles; what differs later is that no row offers them an action.
    """
    assert visible_queues(ACCOUNTANT) == set(QUEUE_TILES)


def test_the_queue_counts_against_the_seeded_data(demo):
    client = client_for(ACCOUNTANT)

    skip = {"promotions", "open-value"}
    counts = {key: count(client, model, params) for key, (model, params) in QUEUE_TILES.items() if key not in skip}

    # The seed puts these numbers there deliberately; see test_seed_catalog.py.
    assert counts == {
        "restock": 15,
        "overdue": 2,
        "review": 1,
    }


def test_the_promotion_tile_counts_what_is_running_today(demo):
    """
    Run against today rather than a fixed date, because the tile does: the seeded spring
    promotion covers September 2026 and the other two are historical.
    """
    running = count(client_for(ACCOUNTANT), "promotion", {"active_on": date.today().isoformat()})

    assert running == (1 if date(2026, 9, 1) <= date.today() < date(2026, 9, 30) else 0)


def test_the_value_tile_reads_the_total_rather_than_the_count(demo):
    """
    The one tile that reports a sum. It is the same request as any other tile plus ``ct``
    naming the total, and the sum arrives in the envelope beside the count: eight orders in
    flight, and what the warehouse has committed to them.
    """
    model, params = QUEUE_TILES["open-value"]
    response = client_for(ACCOUNTANT).get(reverse(f"catalog.{model}-list"), {**params, "ps": 1, "ct": "total_value"})

    assert response.status_code == 200, response.data
    assert response.data["totalRecords"] == 8
    assert response.data["columnTotals"] == {"total_value": Decimal("21238.20")}


def test_the_scale_numbers_describe_the_whole_catalog(demo):
    client = client_for(ACCOUNTANT)

    counts = {key: count(client, model) for key, model in SCALE_TILES.items()}

    assert counts == {"widgets": 63, "variants": 61, "suppliers": 5, "warehouses": 3, "orders": 142}


def test_the_pipeline_band_is_one_request_and_only_for_order_readers(demo):
    """
    The band is a single list request against the summary view: every state, in order,
    with the total in the same response. A role that cannot list orders cannot list the
    summary either, so the whole band disappears rather than rendering empty bars.
    """
    client = client_for(SUPERVISOR)
    response = client.get(reverse("catalog.purchaseorderstatecount-list"), {"ps": 20, "ct": "order_count"})

    assert response.status_code == 200, response.data
    assert [(row["code"], row["order_count"]) for row in response.data["results"]] == [
        ("draft", 3),
        ("submitted", 2),
        ("approved", 3),
        ("received", 133),
        ("cancelled", 1),
    ]
    assert response.data["columnTotals"] == {"order_count": 142}

    for email in SALES_ROLES:
        assert not may_list(client_for(email), "purchaseorderstatecount"), email


def test_a_queue_tile_links_to_the_list_its_number_came_from(demo):
    """
    A tile's params are sent to the list endpoint for the count and handed to the link as
    the route query, so the two cannot drift. This checks the halves agree: the filtered
    list returns exactly the rows the tile counted.
    """
    client = client_for(SUPERVISOR)
    model, params = QUEUE_TILES["overdue"]

    counted = count(client, model, params)
    listed = client.get(reverse(f"catalog.{model}-list"), params)

    assert listed.status_code == 200, listed.data
    assert listed.data["totalRecords"] == counted
    assert {row["reference"] for row in listed.data["results"]} == {"PO-1041", "PO-1048"}
