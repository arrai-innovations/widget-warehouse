from decimal import Decimal

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from vueda.core.filters import VuedaSearchFilterBackend

from widget_warehouse.catalog.filtersets import WidgetFilterSet
from widget_warehouse.catalog.models import Supplier, Widget, WidgetCategory
from widget_warehouse.catalog.viewsets import WidgetViewSet


@pytest.fixture
def widget_catalog():
    category = WidgetCategory.objects.create(code="BEARING", name="Bearing")
    other_category = WidgetCategory.objects.create(code="GEAR", name="Gear")
    supplier = Supplier.objects.create(
        name="Eurobearings GmbH",
        slug="eurobearings-gmbh",
        contact_email="sales@example.com",
    )

    bearing = Widget.objects.create(
        name="Ball Bearing 6204",
        slug="ball-bearing-6204",
        sku="BRG-6204",
        category=category,
        supplier=supplier,
        description="Sealed radial bearing for compact assemblies.",
        unit_price=Decimal("8.90"),
        weight_kg=Decimal("0.120"),
    )
    gear = Widget.objects.create(
        name="Spur Gear 24T",
        slug="spur-gear-24t",
        sku="GR-024",
        category=other_category,
        description="Steel spur gear.",
        unit_price=Decimal("18.00"),
        weight_kg=Decimal("0.420"),
    )

    return bearing, gear


@pytest.mark.django_db
def test_widget_sku_filter_is_case_insensitive_partial(widget_catalog):
    queryset = WidgetFilterSet({"sku": "brg"}, queryset=Widget.objects.order_by("sku")).qs

    assert list(queryset.values_list("sku", flat=True)) == ["BRG-6204"]


@pytest.mark.django_db
def test_widget_sku_exact_filter_remains_available(widget_catalog):
    base_queryset = Widget.objects.order_by("sku")
    exact_queryset = WidgetFilterSet({"sku_exact": "brg-6204"}, queryset=base_queryset).qs
    partial_queryset = WidgetFilterSet({"sku_exact": "brg"}, queryset=base_queryset).qs

    assert list(exact_queryset.values_list("sku", flat=True)) == ["BRG-6204"]
    assert list(partial_queryset.values_list("sku", flat=True)) == []


@pytest.mark.django_db
def test_widget_search_limits_results(widget_catalog, settings):
    request = Request(APIRequestFactory().get("/", {settings.REST_FRAMEWORK["SEARCH_PARAM"]: "brg"}))
    queryset = VuedaSearchFilterBackend().filter_queryset(request, Widget.objects.order_by("sku"), WidgetViewSet())

    assert list(queryset.values_list("sku", flat=True)) == ["BRG-6204"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("params", "expected_skus"),
    [
        ({"unit_price_min": "9.00"}, ["GR-024"]),
        ({"unit_price_max": "10.00"}, ["BRG-6204"]),
        ({"unit_price_min": "8.00", "unit_price_max": "10.00"}, ["BRG-6204"]),
    ],
)
def test_widget_unit_price_range_filter(widget_catalog, params, expected_skus):
    queryset = WidgetFilterSet(params, queryset=Widget.objects.order_by("sku")).qs

    assert list(queryset.values_list("sku", flat=True)) == expected_skus


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("params", "expected_skus"),
    [
        ({"weight_kg_min": "0.200"}, ["GR-024"]),
        ({"weight_kg_max": "0.200"}, ["BRG-6204"]),
        ({"weight_kg_min": "0.100", "weight_kg_max": "0.200"}, ["BRG-6204"]),
    ],
)
def test_widget_weight_range_filter(widget_catalog, params, expected_skus):
    queryset = WidgetFilterSet(params, queryset=Widget.objects.order_by("sku")).qs

    assert list(queryset.values_list("sku", flat=True)) == expected_skus
