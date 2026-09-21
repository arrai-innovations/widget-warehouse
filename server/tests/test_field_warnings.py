"""Catalog warnings withhold writes until acknowledged through VUEDA's standard gate."""

from datetime import date

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from widget_warehouse.catalog.models import (
    InventoryRecord,
    PurchaseOrder,
    PurchaseOrderLine,
    Supplier,
    Warehouse,
    Widget,
    WidgetCategory,
    WidgetVariant,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog():
    supplier = Supplier.objects.create(
        name="Precision Parts", slug="precision", contact_email="sales@example.com", typical_lead_days=14
    )
    warehouse = Warehouse.objects.create(
        name="Central", code="CTR", address="1 Industrial Road", opens_at="08:00", closes_at="17:00"
    )
    widget = Widget.objects.create(
        name="Sprocket",
        sku="SPR",
        category=WidgetCategory.objects.create(name="Sprockets", code="SPR"),
        supplier=supplier,
        unit_price="12.50",
    )
    variant = WidgetVariant.objects.create(widget=widget, name="Standard", sku_suffix="STD")
    return {"supplier": supplier, "warehouse": warehouse, "variant": variant}


@pytest.fixture
def client():
    call_command("seed_demo_users", verbosity=0)
    call_command("seed_workflows", verbosity=0)
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email="clerk@widgetwarehouse.com"))
    return client


@pytest.fixture
def order_data(catalog):
    return {
        "reference": "PO-WARN",
        "supplier": catalog["supplier"].pk,
        "destination_warehouse": catalog["warehouse"].pk,
        "order_date": "2026-09-01",
        "expected_arrival_date": "2026-09-04",
        "lines": [{"variant": catalog["variant"].pk, "quantity_ordered": 10, "unit_price": "12.50"}],
    }


@pytest.fixture
def order(catalog):
    return PurchaseOrder.objects.create(
        reference="PO-WARN",
        supplier=catalog["supplier"],
        destination_warehouse=catalog["warehouse"],
        order_date=date(2026, 9, 1),
        expected_arrival_date=date(2026, 9, 15),
    )


def order_url(pk=None):
    route = reverse("catalog.purchaseorder-detail", args=[pk]) if pk else reverse("catalog.purchaseorder-list")
    return f"{route}?{settings.REST_FLEX_FIELDS['EXPAND_PARAM']}=lines"


@pytest.mark.parametrize(
    ("arrival", "lead_days", "expected_message"),
    [
        (
            "2026-09-04",
            14,
            "Expected delivery is 3 days after the order date; this supplier's typical lead time is 14 days.",
        ),
        (
            "2026-09-02",
            14,
            "Expected delivery is 1 day after the order date; this supplier's typical lead time is 14 days.",
        ),
        (
            "2026-09-01",
            1,
            "Expected delivery is 0 days after the order date; this supplier's typical lead time is 1 day.",
        ),
    ],
)
def test_early_delivery_create_requires_confirmation_before_saving_order_and_lines(
    client, catalog, order_data, arrival, lead_days, expected_message
):
    supplier = catalog["supplier"]
    supplier.typical_lead_days = lead_days
    supplier.save()
    order_data["expected_arrival_date"] = arrival
    response = client.post(order_url(), order_data, format="json")

    assert response.status_code == 409, response.data
    assert response.data["confirmation_required"] is True
    assert response.data["warnings"] == {
        "expected_arrival_date": [f"{expected_message} Confirm that the earlier delivery has been arranged."]
    }
    # Cancelling means no retry. Neither the parent nor the nested lines have been saved.
    assert not PurchaseOrder.objects.exists()
    assert not PurchaseOrderLine.objects.exists()

    confirmed = client.post(
        order_url(), order_data, format="json", headers={"Acknowledge-Warnings": response.data["digest"]}
    )
    assert confirmed.status_code == 201, confirmed.data
    assert PurchaseOrder.objects.get().expected_arrival_date == date.fromisoformat(arrival)
    assert PurchaseOrderLine.objects.get().quantity_ordered == 10


@pytest.mark.parametrize(
    ("arrival", "lead_days"),
    [("2026-09-15", 14), ("2026-09-16", 14), (None, 14), ("2026-09-04", None), ("2026-09-01", 0)],
)
def test_delivery_without_a_short_lead_time_saves_normally(client, catalog, order_data, arrival, lead_days):
    supplier = catalog["supplier"]
    supplier.typical_lead_days = lead_days
    supplier.save()
    order_data["expected_arrival_date"] = arrival

    response = client.post(order_url(), order_data, format="json")

    assert response.status_code == 201, response.data


@pytest.mark.parametrize("changed_field", ["expected_arrival_date", "order_date", "supplier"])
def test_delivery_patch_checks_saved_values_and_confirms(client, catalog, order, changed_field):
    slower_supplier = Supplier.objects.create(
        name="Slow Parts", slug="slow", contact_email="sales@example.com", typical_lead_days=21
    )
    changes = {
        "expected_arrival_date": "2026-09-04",
        "order_date": "2026-09-10",
        "supplier": slower_supplier.pk,
    }
    payload = {changed_field: changes[changed_field]}
    original = (order.supplier_id, order.order_date, order.expected_arrival_date)

    response = client.patch(order_url(order.pk), payload, format="json")

    assert response.status_code == 409, response.data
    assert set(response.data["warnings"]) == {"expected_arrival_date"}
    order.refresh_from_db()
    assert (order.supplier_id, order.order_date, order.expected_arrival_date) == original

    confirmed = client.patch(
        order_url(order.pk), payload, format="json", headers={"Acknowledge-Warnings": response.data["digest"]}
    )
    assert confirmed.status_code == 200, confirmed.data
    order.refresh_from_db()
    saved = order.supplier_id if changed_field == "supplier" else str(getattr(order, changed_field))
    assert saved == changes[changed_field]


@pytest.mark.parametrize("method", ["patch", "put"])
def test_unrelated_order_edits_do_not_repeat_delivery_warning(client, order, order_data, method):
    order.expected_arrival_date = date(2026, 9, 4)
    order.save()
    payload = {"reference": "PO-RENAMED"}
    if method == "put":
        payload = {**order_data, **payload}

    response = getattr(client, method)(order_url(order.pk), payload, format="json")

    assert response.status_code == 200, response.data
    order.refresh_from_db()
    assert order.reference == "PO-RENAMED"


@pytest.fixture
def inventory_client():
    call_command("seed_demo_users", verbosity=0)
    user = get_user_model().objects.get(email="supervisor@widgetwarehouse.com")
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def inventory_creator(inventory_client):
    # Creation also exercises the warning contract, but is not a demo role capability.
    user = get_user_model().objects.get(email="supervisor@widgetwarehouse.com")
    user.user_permissions.add(
        Permission.objects.get(content_type__app_label="catalog", codename="create_inventoryrecord")
    )
    inventory_client.force_authenticate(user)
    return inventory_client


@pytest.fixture
def stock_data(catalog):
    return {
        "variant": catalog["variant"].pk,
        "warehouse": catalog["warehouse"].pk,
        "quantity_on_hand": 140,
        "max_stock_level": 100,
    }


@pytest.mark.parametrize(("quantity", "maximum", "stock_text"), [(140, 100, "140 units"), (1, 0, "1 unit")])
def test_overstock_create_requires_confirmation(inventory_creator, stock_data, quantity, maximum, stock_text):
    stock_data.update(quantity_on_hand=quantity, max_stock_level=maximum)
    url = reverse("catalog.inventoryrecord-list")
    response = inventory_creator.post(url, stock_data, format="json")

    assert response.status_code == 409, response.data
    assert response.data["confirmation_required"] is True
    assert response.data["warnings"] == {
        "quantity_on_hand": [
            f"Recorded stock is {stock_text}, above this location's maximum stock level of {maximum}. "
            "Confirm that the count is correct."
        ]
    }
    assert not InventoryRecord.objects.exists()

    confirmed = inventory_creator.post(
        url, stock_data, format="json", headers={"Acknowledge-Warnings": response.data["digest"]}
    )
    assert confirmed.status_code == 201, confirmed.data
    assert InventoryRecord.objects.get().quantity_on_hand == quantity


@pytest.mark.parametrize(("quantity", "maximum"), [(100, 100), (99, 100), (140, None), (0, 0)])
def test_stock_within_maximum_or_without_maximum_saves_normally(inventory_creator, stock_data, quantity, maximum):
    stock_data.update(quantity_on_hand=quantity, max_stock_level=maximum)

    response = inventory_creator.post(reverse("catalog.inventoryrecord-list"), stock_data, format="json")

    assert response.status_code == 201, response.data


@pytest.mark.parametrize("payload", [{"quantity_on_hand": 140}, {"max_stock_level": 0}])
def test_overstock_patch_checks_saved_values_and_confirms(inventory_client, catalog, payload):
    stock = InventoryRecord.objects.create(
        variant=catalog["variant"], warehouse=catalog["warehouse"], quantity_on_hand=80, max_stock_level=100
    )
    url = reverse("catalog.inventoryrecord-detail", args=[stock.pk])

    response = inventory_client.patch(url, payload, format="json")

    assert response.status_code == 409, response.data
    assert set(response.data["warnings"]) == {"quantity_on_hand"}
    stock.refresh_from_db()
    assert (stock.quantity_on_hand, stock.max_stock_level) == (80, 100)

    confirmed = inventory_client.patch(
        url, payload, format="json", headers={"Acknowledge-Warnings": response.data["digest"]}
    )
    assert confirmed.status_code == 200, confirmed.data
    stock.refresh_from_db()
    for field, value in payload.items():
        assert getattr(stock, field) == value


@pytest.mark.parametrize("method", ["patch", "put"])
def test_unrelated_stock_edits_do_not_repeat_overstock_warning(inventory_client, catalog, stock_data, method):
    stock = InventoryRecord.objects.create(
        variant=catalog["variant"], warehouse=catalog["warehouse"], quantity_on_hand=140, max_stock_level=100
    )
    payload = {"notes": "Counted twice."}
    if method == "put":
        payload = {**stock_data, **payload}

    response = getattr(inventory_client, method)(
        reverse("catalog.inventoryrecord-detail", args=[stock.pk]), payload, format="json"
    )

    assert response.status_code == 200, response.data
    stock.refresh_from_db()
    assert stock.notes == "Counted twice."


def test_changed_stock_warning_requires_a_new_acknowledgement(inventory_creator, stock_data):
    url = reverse("catalog.inventoryrecord-list")
    original = inventory_creator.post(url, stock_data, format="json")
    assert original.status_code == 409, original.data
    stock_data["quantity_on_hand"] = 150

    changed = inventory_creator.post(
        url, stock_data, format="json", headers={"Acknowledge-Warnings": original.data["digest"]}
    )

    assert changed.status_code == 409, changed.data
    assert changed.data["digest"] != original.data["digest"]
    assert not InventoryRecord.objects.exists()


def test_invalid_stock_is_rejected_before_warnings(inventory_creator, stock_data):
    stock_data["quantity_on_hand"] = -1

    response = inventory_creator.post(reverse("catalog.inventoryrecord-list"), stock_data, format="json")

    assert response.status_code == 400, response.data
    assert "quantity_on_hand" in response.data
    assert not InventoryRecord.objects.exists()
