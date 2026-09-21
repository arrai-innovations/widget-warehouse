"""The report shares order-list filters, authorization and exact decimal totals."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient
from vueda.workflow.models import State, StatePermission

from tests.test_dashboard_tiles import ACCOUNTANT, ASSOCIATE, client_for
from widget_warehouse.catalog.models import PurchaseOrder, PurchaseOrderLine


@pytest.fixture
def demo(db):
    call_command("seed_demo_users", verbosity=0)
    call_command("seed_workflows", verbosity=0)
    call_command("seed_catalog", verbosity=0)


def params(weeks=6):
    today = datetime.now(UTC).date()
    monday = today - timedelta(days=today.weekday())
    return {
        "order_date_after": (monday - timedelta(weeks=weeks)).isoformat(),
        "order_date_before": (monday - timedelta(days=1)).isoformat(),
        "purchasing": "true",
    }


def report(client, query=None):
    return client.get(reverse("catalog.purchasing-trend"), query or params())


def test_report_matches_full_filtered_order_totals_and_week_links(demo):
    client = client_for(ACCOUNTANT)
    response = report(client, {**params(), "ps": 1})
    assert response.status_code == 200, response.data
    rows = response.data["results"]
    assert len(rows) == 5
    assert response.data["totalPages"] == 1
    assert [row["code"] for row in rows] == sorted(row["code"] for row in rows)
    assert len({row["id"] for row in rows}) == 5
    for row in rows:
        assert len(row["values"]) == 6
        for observation in row["values"]:
            week = date.fromisoformat(observation["week"])
            assert week.weekday() == 0
            matching = client.get(
                reverse("catalog.purchaseorder-list"),
                {
                    "supplier": row["id"],
                    "purchasing": "true",
                    "ps": 1,
                    "order_date_after": week.isoformat(),
                    "order_date_before": (week + timedelta(days=6)).isoformat(),
                },
            )
            assert matching.status_code == 200, matching.data
            assert Decimal(observation["value"]) == matching.data["columnTotals"]["total_value"]


def test_report_zero_fills_an_absent_week_and_empty_period(demo):
    first = report(client_for(ACCOUNTANT)).data["results"][0]
    start = params()["order_date_after"]
    end = (date.fromisoformat(start) + timedelta(days=6)).isoformat()
    PurchaseOrderLine.objects.filter(
        purchase_order__supplier_id=first["id"],
        purchase_order__order_date__range=(start, end),
    ).delete()
    rows = report(client_for(ACCOUNTANT)).data["results"]
    assert rows[0]["values"][0] == {"week": start, "value": "0.00"}
    PurchaseOrderLine.objects.all().delete()
    assert report(client_for(ACCOUNTANT)).data["results"] == []


def test_report_enforces_list_permission_and_workflow_row_visibility(demo):
    assert report(APIClient()).status_code in (401, 403)
    assert report(client_for(ASSOCIATE)).status_code == 403
    state = State.objects.get(workflow__content_type=PurchaseOrder.get_content_type(), code="received")
    # Use the actual demo group rather than bypassing its authorization with a superuser.
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.get(email=ACCOUNTANT)
    group = user.groups.first()
    assert isinstance(group, Group)
    permission = Permission.objects.get(content_type=PurchaseOrder.get_content_type(), codename="list_purchaseorder")
    StatePermission.objects.create(state=state, group=group, permission=permission, grant_or_deny=False)
    response = report(client_for(ACCOUNTANT))
    assert response.status_code == 200, response.data
    total = sum(Decimal(value["value"]) for row in response.data["results"] for value in row["values"])
    orders = client_for(ACCOUNTANT).get(reverse("catalog.purchaseorder-list"), {**params(), "ps": 1})
    assert total == orders.data["columnTotals"]["total_value"]
    assert total < Decimal("20000")
    pipeline = client_for(ACCOUNTANT).get(reverse("catalog.order-pipeline"), params())
    assert pipeline.status_code == 200, pipeline.data
    assert pipeline.data["columnTotals"]["order_count"] == orders.data["totalRecords"]


@pytest.mark.parametrize(
    "override",
    [
        {"order_date_after": "invalid"},
        {"order_date_before": "2099-01-01"},
        {"order_date_after": "2020-01-06"},
        {"purchasing": "false"},
        {"order_date_after": "2026-09-01", "order_date_before": "2026-09-06"},
    ],
)
def test_report_rejects_incomplete_or_unbounded_periods(demo, override):
    assert report(client_for(ACCOUNTANT), {**params(), **override}).status_code == 400


def test_pipeline_period_counts_and_drill_down_links_agree(demo):
    client = client_for(ACCOUNTANT)
    today = datetime.now(UTC).date()
    query = {"order_date_after": (today - timedelta(days=29)).isoformat(), "order_date_before": today.isoformat()}
    response = client.get(reverse("catalog.order-pipeline"), query)
    assert response.status_code == 200, response.data
    assert [row["code"] for row in response.data["results"]] == [
        "draft",
        "submitted",
        "approved",
        "received",
        "cancelled",
    ]
    for row in response.data["results"]:
        matching = client.get(reverse("catalog.purchaseorder-list"), {**query, "workflow_state": row["id"], "ps": 1})
        assert matching.status_code == 200, matching.data
        assert row["order_count"] == matching.data["totalRecords"]
    all_time = client.get(reverse("catalog.order-pipeline"))
    assert all_time.data["columnTotals"]["order_count"] == 142
    assert response.data["columnTotals"]["order_count"] < 40
    empty = client.get(reverse("catalog.order-pipeline"), {"order_date_before": "2000-01-01"})
    assert len(empty.data["results"]) == 5
    assert empty.data["columnTotals"]["order_count"] == 0
    assert all(row["order_count"] == 0 for row in empty.data["results"])
    assert client_for(ASSOCIATE).get(reverse("catalog.order-pipeline")).status_code == 403
    assert client.get(reverse("catalog.order-pipeline"), {"order_date_after": "invalid"}).status_code == 400
