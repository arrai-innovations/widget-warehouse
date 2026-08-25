from decimal import Decimal

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from widget_warehouse.catalog.models import InventoryRecord, Warehouse, Widget, WidgetCategory, WidgetVariant
from widget_warehouse.catalog.serializers import InventoryRecordSerializer, WidgetVariantSerializer

EXPAND_PARAM = settings.REST_FLEX_FIELDS["EXPAND_PARAM"]


@pytest.fixture
def catalog(db):
    widget = Widget.objects.create(
        name="Standard Sprocket",
        slug="standard-sprocket",
        sku="SPR-100",
        category=WidgetCategory.objects.create(code="SPROCKET", name="Sprocket"),
        unit_price=Decimal("12.50"),
    )
    variant = WidgetVariant.objects.create(widget=widget, name="Small (8T)", sku_suffix="SM")
    warehouse = Warehouse.objects.create(
        name="Sydney Distribution Centre",
        code="SYD-DC",
        address="42 Industrial Drive",
        opens_at="07:00",
        closes_at="18:00",
    )
    inventory_record = InventoryRecord.objects.create(variant=variant, warehouse=warehouse, quantity_on_hand=25)
    return {
        "inventory_record": inventory_record,
        "variant": variant,
        "warehouse": warehouse,
        "widget": widget,
    }


@pytest.fixture
def api_client(db):
    user = get_user_model().objects.create_superuser(
        email="admin@example.com",
        password="password",
        name="Admin",
    )
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.mark.parametrize(
    ("serializer_class", "expected_expands"),
    (
        (WidgetVariantSerializer, {"widget"}),
        (InventoryRecordSerializer, {"variant", "warehouse"}),
    ),
)
def test_list_foreign_keys_have_minimal_expansion_metadata(serializer_class, expected_expands):
    expands = {expand["name"]: expand for expand in serializer_class().generate_expand_model_info()}

    assert set(expands) == expected_expands
    for expand in expands.values():
        assert set(expand["f"]) == {"id", "formatted_name"}


@pytest.mark.django_db
def test_widget_variant_list_expands_widget_label(api_client, catalog):
    response = api_client.get(
        reverse("catalog.widgetvariant-list"),
        data={EXPAND_PARAM: "widget"},
    )

    assert response.status_code == 200, response.data
    expanded_widget = response.data["results"][0]["widget"]
    assert expanded_widget["id"] == catalog["widget"].id
    assert expanded_widget["formatted_name"] == "Standard Sprocket"


@pytest.mark.django_db
def test_inventory_record_list_expands_foreign_key_labels(api_client, catalog):
    response = api_client.get(
        reverse("catalog.inventoryrecord-list"),
        data={EXPAND_PARAM: "variant,warehouse"},
    )

    assert response.status_code == 200, response.data
    result = response.data["results"][0]
    assert result["variant"]["id"] == catalog["variant"].id
    assert result["variant"]["formatted_name"] == "Small (8T)"
    assert result["warehouse"]["id"] == catalog["warehouse"].id
    assert result["warehouse"]["formatted_name"] == "Sydney Distribution Centre"
