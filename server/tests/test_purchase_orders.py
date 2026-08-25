"""
Contract tests for the purchase order's writable inline.

The lines relation is only reachable through the parent order, so these cover the
behaviour an integrator has to know about it: the expand parameter is what makes a
nested payload deserialize as objects, and a line left out of an update is deleted.
"""

from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import urlencode

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from widget_warehouse.catalog.models import (
    PurchaseOrder,
    PurchaseOrderLine,
    Supplier,
    Warehouse,
    Widget,
    WidgetCategory,
    WidgetVariant,
)

EXPAND_PARAM = settings.REST_FLEX_FIELDS["EXPAND_PARAM"]
FIELDS_PARAM = settings.REST_FLEX_FIELDS["FIELDS_PARAM"]
LIST_URL = f"{{}}?{EXPAND_PARAM}=lines"

# The request the client's storeModelInfo makes for every screen it builds.
MODEL_INFO_SECTIONS = (
    "model_fields",
    "model_actions",
    "model_expands",
    "model_ordering",
    "model_filtering",
    "model_permissions",
)
MODEL_INFO_QUERY = urlencode(
    [(FIELDS_PARAM, section) for section in ("app_label", "model", *MODEL_INFO_SECTIONS)]
    + [(EXPAND_PARAM, section) for section in MODEL_INFO_SECTIONS]
)


@pytest.fixture
def catalog(db):
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
    widget = Widget.objects.create(
        name="Standard Sprocket",
        slug="standard-sprocket",
        sku="SPR-100",
        category=WidgetCategory.objects.create(code="SPROCKET", name="Sprocket"),
        supplier=supplier,
        unit_price=Decimal("12.50"),
    )
    small = WidgetVariant.objects.create(widget=widget, name="Small (8T)", sku_suffix="SM")
    medium = WidgetVariant.objects.create(widget=widget, name="Medium (12T)", sku_suffix="MD")

    return {"supplier": supplier, "warehouse": warehouse, "small": small, "medium": medium}


@pytest.fixture
def seeded_roles(db):
    call_command("seed_demo_users", verbosity=0)


def client_for(email):
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=email))
    return client


def order_payload(catalog, reference="PO-1042", lines=None):
    return {
        "reference": reference,
        "supplier": catalog["supplier"].id,
        "destination_warehouse": catalog["warehouse"].id,
        "order_date": str(date(2026, 9, 1)),
        "expected_arrival_date": str(date(2026, 9, 1) + timedelta(days=14)),
        "lines": lines if lines is not None else [],
    }


@pytest.mark.django_db
def test_clerk_creates_an_order_and_its_lines_in_one_request(catalog, seeded_roles):
    payload = order_payload(
        catalog,
        lines=[
            {"variant": catalog["small"].id, "quantity_ordered": 120, "unit_price": "12.50"},
            {"variant": catalog["medium"].id, "quantity_ordered": 80, "unit_price": "14.50"},
        ],
    )

    response = client_for("clerk@widgetwarehouse.com").post(
        LIST_URL.format(reverse("catalog.purchaseorder-list")),
        payload,
        format="json",
    )

    assert response.status_code == 201, response.data
    order = PurchaseOrder.objects.get(reference="PO-1042")
    assert sorted(order.lines.values_list("quantity_ordered", flat=True)) == [80, 120]


@pytest.mark.django_db
def test_update_applies_changed_and_added_lines_and_deletes_omitted_ones(catalog, seeded_roles):
    client = client_for("clerk@widgetwarehouse.com")
    list_url = LIST_URL.format(reverse("catalog.purchaseorder-list"))
    created = client.post(
        list_url,
        order_payload(
            catalog,
            lines=[
                {"variant": catalog["small"].id, "quantity_ordered": 120, "unit_price": "12.50"},
                {"variant": catalog["medium"].id, "quantity_ordered": 80, "unit_price": "14.50"},
            ],
        ),
        format="json",
    )
    assert created.status_code == 201, created.data
    order = PurchaseOrder.objects.get(reference="PO-1042")
    kept, omitted = order.lines.order_by("id")

    # The kept line carries its id, so it is updated in place. The omitted line's id is
    # absent from the payload, which deletes it.
    response = client.put(
        LIST_URL.format(reverse("catalog.purchaseorder-detail", args=[order.id])),
        order_payload(
            catalog,
            lines=[
                {"id": kept.id, "variant": kept.variant_id, "quantity_ordered": 150, "unit_price": "12.75"},
                {"variant": catalog["medium"].id, "quantity_ordered": 40, "unit_price": "14.00"},
            ],
        ),
        format="json",
    )

    assert response.status_code == 200, response.data
    kept.refresh_from_db()
    assert kept.quantity_ordered == 150
    assert not PurchaseOrderLine.objects.filter(id=omitted.id).exists()
    assert order.lines.count() == 2


@pytest.mark.django_db
def test_nested_line_objects_without_the_expand_parameter_are_rejected(catalog, seeded_roles):
    payload = order_payload(
        catalog,
        lines=[{"variant": catalog["small"].id, "quantity_ordered": 120, "unit_price": "12.50"}],
    )

    response = client_for("clerk@widgetwarehouse.com").post(
        reverse("catalog.purchaseorder-list"),
        payload,
        format="json",
    )

    assert response.status_code == 400, response.data
    assert "lines" in response.data


@pytest.mark.django_db
def test_sales_roles_cannot_write_purchase_orders(catalog, seeded_roles):
    response = client_for("associate@widgetwarehouse.com").post(
        LIST_URL.format(reverse("catalog.purchaseorder-list")),
        order_payload(catalog),
        format="json",
    )

    assert response.status_code == 403, response.data
    assert not PurchaseOrder.objects.exists()


@pytest.mark.django_db
def test_model_info_reports_the_permitted_actions_and_the_lines_inline(catalog, seeded_roles):
    """
    Model info is what the client builds the nav, the list, and the forms from, and a model
    is only served here if it was registered in the app config. Without that registration
    every purchase order screen 404s before any permission is consulted.
    """
    url = reverse("info.model_info-detail", kwargs={"app_label": "catalog", "model": "purchaseorder"})

    response = client_for("clerk@widgetwarehouse.com").get(f"{url}?{MODEL_INFO_QUERY}")

    assert response.status_code == 200, response.data
    assert {"list", "create", "update"} <= {action["name"] for action in response.data["model_actions"]}
    lines = next(expand for expand in response.data["model_expands"] if expand["name"] == "lines")
    assert lines["many"]
    assert not lines["read_only"]
    assert {"id", "variant", "quantity_ordered", "unit_price"} <= set(lines["f"])

    # The sales roles are granted nothing on purchase orders, so model info reports no
    # actions and the nav drops the entry rather than the client filtering it out.
    associate_response = client_for("associate@widgetwarehouse.com").get(f"{url}?{MODEL_INFO_QUERY}")
    assert associate_response.status_code == 200, associate_response.data
    assert associate_response.data["model_actions"] == []
