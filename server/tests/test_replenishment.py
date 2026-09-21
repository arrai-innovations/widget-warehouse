import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from tests import test_inventory, test_purchase_order_workflow
from widget_warehouse.catalog.models import InventoryRecord, PurchaseOrder, ReplenishmentBatch, SupplierPrice, Warehouse

pytestmark = pytest.mark.django_db
stock = test_inventory.stock


@pytest.fixture
def scenario(stock):
    call_command("seed_demo_users", verbosity=0)
    call_command("seed_workflows", verbosity=0)
    record = stock["short"]
    record.max_stock_level = 40
    record.save()
    supplier = record.variant.widget.supplier
    supplier.is_approved = True
    supplier.save()
    price = SupplierPrice.objects.create(supplier=supplier, variant=record.variant, unit_cost="4.25")
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email="clerk@widgetwarehouse.com"))
    return client, record, price


def endpoint():
    return reverse("catalog.inventoryrecord-replenish")


def proposal(client, *records):
    response = client.get(endpoint(), {"pks": ",".join(str(record.pk) for record in records)})
    assert response.status_code == 200, response.data
    return response.data["rows"]


def payload(rows):
    return {
        "batch_id": str(uuid.uuid4()),
        "lines": [
            {
                "inventory_id": row["inventory_id"],
                "quantity": row["quantity"],
                "unit_price": row["unit_price"],
                "snapshot": row["snapshot"],
            }
            for row in rows
        ],
    }


def test_preview_and_dry_run_write_nothing(scenario):
    client, record, _ = scenario
    rows = proposal(client, record)
    assert rows[0]["quantity"] == 38
    assert rows[0]["unit_price"] == "4.25"
    assert not ReplenishmentBatch.objects.exists()
    response = client.post(endpoint(), payload(rows), format="json", HTTP_DRY_RUN="true")
    assert response.status_code == 200, response.data
    assert response.data == {"order_count": 1}
    assert not PurchaseOrder.objects.exists()
    assert not ReplenishmentBatch.objects.exists()


def test_execution_creates_draft_with_override_and_retry_returns_same_batch(scenario):
    client, record, price = scenario
    data = payload(proposal(client, record))
    data["lines"][0]["unit_price"] = "3.99"
    first = client.post(endpoint(), data, format="json")
    assert first.status_code == 200, first.data
    second = client.post(endpoint(), data, format="json")
    assert second.status_code == 200, second.data
    assert second.data == first.data
    order = PurchaseOrder.objects.get()
    assert order.object_states_proxy.get().state.code == "draft"
    assert order.lines.get().unit_price == Decimal("3.99")
    price.refresh_from_db()
    assert price.unit_cost == Decimal("4.25")
    after = proposal(client, record)[0]
    assert after["pending"] == 38
    assert after["incoming"] == 0
    assert after["quantity"] == 0
    listed = client.get(reverse("catalog.purchaseorder-list"), {"replenishment_batch": first.data["batch_id"]})
    assert listed.status_code == 200, listed.data
    assert [row["id"] for row in listed.data["results"]] == [order.pk]


def test_separate_submissions_from_same_preview_cannot_order_twice(scenario):
    client, record, _ = scenario
    data = payload(proposal(client, record))
    assert client.post(endpoint(), data, format="json").status_code == 200
    data["batch_id"] = str(uuid.uuid4())
    response = client.post(endpoint(), data, format="json")
    assert response.status_code == 400, response.data
    assert PurchaseOrder.objects.count() == 1
    assert ReplenishmentBatch.objects.count() == 1


def test_stale_stock_requires_new_review(scenario):
    client, record, _ = scenario
    data = payload(proposal(client, record))
    record.quantity_on_hand = 5
    record.save()
    response = client.post(endpoint(), data, format="json")
    assert response.status_code == 400, response.data
    assert not PurchaseOrder.objects.exists()
    assert not ReplenishmentBatch.objects.exists()


def test_group_by_supplier_and_warehouse(scenario, stock):
    client, record, _ = scenario
    second = stock["exactly_at"]
    second.quantity_on_hand = 1
    second.save()
    warehouse = Warehouse.objects.create(
        name="Second", code="SECOND", address="Second", opens_at="07:00", closes_at="18:00"
    )
    third = InventoryRecord.objects.create(
        variant=record.variant, warehouse=warehouse, quantity_on_hand=1, reorder_threshold=10
    )
    rows = proposal(client, record, second, third)
    # Missing defaults can be filled with an explicitly reviewed price.
    data = payload(rows)
    for line in data["lines"]:
        line["unit_price"] = "2.00"
    response = client.post(endpoint(), data, format="json")
    assert response.status_code == 200, response.data
    assert PurchaseOrder.objects.count() == 2
    assert sorted(order.lines.count() for order in PurchaseOrder.objects.all()) == [1, 2]


@pytest.mark.parametrize("change", ["negative_price", "too_many", "duplicate", "missing_price"])
def test_invalid_submission_is_atomic(scenario, change):
    client, record, _ = scenario
    data = payload(proposal(client, record))
    if change == "negative_price":
        data["lines"][0]["unit_price"] = "-1"
    elif change == "too_many":
        data["lines"][0]["quantity"] = 9999
    elif change == "duplicate":
        data["lines"].append(data["lines"][0].copy())
    else:
        data["lines"][0]["unit_price"] = None
    response = client.post(endpoint(), data, format="json")
    assert response.status_code == 400, response.data
    assert not ReplenishmentBatch.objects.exists()
    assert not PurchaseOrder.objects.exists()


def test_readonly_user_cannot_replenish_or_discover_action(scenario):
    client, record, _ = scenario
    client.force_authenticate(get_user_model().objects.get(email="accountant@widgetwarehouse.com"))
    assert client.get(endpoint(), {"pks": record.pk}).status_code == 403
    assert client.post(endpoint(), {}, format="json").status_code == 403
    response = client.get(reverse("catalog.inventoryrecord-list"))
    assert response.status_code == 200
    info = client.get("/routes/vueda.info/model_info/catalog/inventoryrecord/?e=model_actions")
    assert info.status_code == 200, info.data
    assert "replenish" not in [action["name"] for action in info.data["model_actions"]]


def test_ordinary_po_defaults_price_but_preserves_custom_price(scenario):
    client, record, price = scenario
    data = {
        "reference": "DEFAULT-COST",
        "supplier": price.supplier_id,
        "destination_warehouse": record.warehouse_id,
        "order_date": "2026-09-20",
        "lines": [{"variant": record.variant_id, "quantity_ordered": 2}],
    }
    response = client.post(reverse("catalog.purchaseorder-list") + "?e=lines", data, format="json")
    assert response.status_code == 201, response.data
    order = PurchaseOrder.objects.get(reference="DEFAULT-COST")
    assert order.lines.get().unit_price == Decimal("4.25")
    data["reference"] = "CUSTOM-COST"
    data["lines"][0]["unit_price"] = "0.00"
    assert client.post(reverse("catalog.purchaseorder-list") + "?e=lines", data, format="json").status_code == 201
    assert PurchaseOrder.objects.get(reference="CUSTOM-COST").lines.get().unit_price == 0
    price.unit_cost = "10.00"
    price.save()
    assert order.lines.get().unit_price == Decimal("4.25")


def test_stock_labels_and_changed_supplier_cost(scenario):
    client, record, price = scenario
    rows = proposal(client, record)
    assert rows[0]["name"] == "SPR-100-SM @ SYD-DC"
    price.unit_cost = "5.00"
    price.save()
    response = client.post(endpoint(), payload(rows), format="json")
    assert response.status_code == 400
    assert not PurchaseOrder.objects.exists()


def test_approved_coverage_is_incoming_and_cancelled_orders_do_not_cover(scenario):
    from vueda.workflow.models import ObjectState, State

    client, record, _ = scenario
    data = payload(proposal(client, record))
    assert client.post(endpoint(), data, format="json").status_code == 200
    order = PurchaseOrder.objects.get()
    state = ObjectState.objects.get(pk=order.object_states_proxy.get().object_state_id)
    state.state = State.objects.get(workflow=state.state.workflow, code="approved")
    state.save()
    row = proposal(client, record)[0]
    assert (row["incoming"], row["pending"], row["quantity"]) == (38, 0, 0)
    state.state = State.objects.get(workflow=state.state.workflow, code="cancelled")
    state.save()
    row = proposal(client, record)[0]
    assert (row["incoming"], row["pending"], row["quantity"]) == (0, 0, 38)


@pytest.mark.parametrize("existing_state", [None, "draft", "approved"])
def test_walkthrough_creates_shortage_and_approves_order_with_existing_coverage(scenario, existing_state):
    clerk, record, _ = scenario
    supervisor = test_purchase_order_workflow.client_for("supervisor@widgetwarehouse.com")
    if existing_state:
        existing = clerk.post(endpoint(), payload(proposal(clerk, record)), format="json")
        assert existing.status_code == 200, existing.data
        if existing_state == "approved":
            order = PurchaseOrder.objects.get(pk=existing.data["orders"][0]["id"])
            for transition in ("submit", "approve"):
                response = test_purchase_order_workflow.run_transition(
                    "supervisor@widgetwarehouse.com", order, transition
                )
                assert response.status_code == 200, response.data

    # Preview is also available for a healthy row, before a new shortage is created.
    record.reorder_threshold = 0
    record.save()
    before = proposal(supervisor, record)[0]
    projected = before["on_hand"] + before["incoming"] + before["pending"]
    updated = supervisor.patch(
        reverse("catalog.inventoryrecord-detail", args=[record.pk]),
        {"reorder_threshold": projected + 10, "max_stock_level": projected + 20},
        format="json",
    )
    assert updated.status_code == 200, updated.data
    shortages = clerk.get(reverse("catalog.inventoryrecord-list"), {"below_reorder": "true"})
    assert record.pk in {row["id"] for row in shortages.data["results"]}

    rows = proposal(clerk, record)
    assert rows[0]["quantity"] == 20
    assert rows[0]["issue"] is None
    created = clerk.post(endpoint(), payload(rows), format="json")
    assert created.status_code == 200, created.data
    order = PurchaseOrder.objects.get(pk=created.data["orders"][0]["id"])
    pending = proposal(clerk, record)[0]
    assert pending["pending"] == before["pending"] + 20
    assert pending["quantity"] == 0
    for email, transition in (("clerk@widgetwarehouse.com", "submit"), ("supervisor@widgetwarehouse.com", "approve")):
        response = test_purchase_order_workflow.run_transition(email, order, transition)
        assert response.status_code == 200, response.data

    approved = proposal(clerk, record)[0]
    assert approved["incoming"] == before["incoming"] + 20
    assert approved["pending"] == before["pending"]
    assert approved["quantity"] == 0
    assert approved["issue"] == "Existing orders already cover the reorder threshold."
    record.refresh_from_db()
    assert record.quantity_on_hand == before["on_hand"]


@pytest.mark.django_db(transaction=True)
def test_competing_batches_cannot_replenish_the_same_snapshot(scenario):
    from concurrent.futures import ThreadPoolExecutor

    from django.db import close_old_connections

    client, record, _ = scenario
    rows = proposal(client, record)
    user_id = get_user_model().objects.get(email="clerk@widgetwarehouse.com").pk

    def submit(data):
        close_old_connections()
        try:
            caller = APIClient()
            caller.force_authenticate(get_user_model().objects.get(pk=user_id))
            return caller.post(endpoint(), data, format="json").status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(submit, [payload(rows), payload(rows)]))
    assert sorted(statuses) == [200, 400]
    assert PurchaseOrder.objects.count() == 1
    assert ReplenishmentBatch.objects.count() == 1
