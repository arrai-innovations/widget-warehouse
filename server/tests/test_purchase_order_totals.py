"""
Contract tests for the purchase order's annotated value column and its list total.

``total_value`` is the project's example of an aggregate that is not a column. It is a
subquery annotation over the order's lines, a serializer field of the same name, and a
``column_totals`` entry, and it takes all three to reach the list footer. These pin the
number itself, the three places it has to agree, and the two ways it could silently go
wrong: a join fanning the sum out, and a write response with no annotation behind it.
"""

from datetime import date
from decimal import Decimal
from urllib.parse import urlencode

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
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
from widget_warehouse.catalog.seeding import DemoUsers, PurchaseOrderWorkflow

SUPERVISOR = "supervisor@widgetwarehouse.com"
EXPAND_PARAM = settings.REST_FLEX_FIELDS["EXPAND_PARAM"]
ORDERING_PARAM = settings.REST_FRAMEWORK["ORDERING_PARAM"]
FIELDS_PARAM = settings.REST_FLEX_FIELDS["FIELDS_PARAM"]
MODEL_INFO_QUERY = urlencode(
    [(FIELDS_PARAM, "model_fields"), (EXPAND_PARAM, "model_fields")],
)


@pytest.fixture
def orders(db):
    DemoUsers().run()
    PurchaseOrderWorkflow().run()
    category = WidgetCategory.objects.create(code="SPROCKET", name="Sprocket")
    supplier = Supplier.objects.create(
        name="Precision Parts Co.",
        slug="precision-parts-co",
        contact_email="sales@example.com",
    )
    other_supplier = Supplier.objects.create(
        name="Pacific Fasteners Ltd.",
        slug="pacific-fasteners",
        contact_email="orders@example.com",
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
        category=category,
        supplier=supplier,
        unit_price="12.50",
    )

    def variant(suffix):
        return WidgetVariant.objects.create(widget=widget, name=suffix, sku_suffix=suffix)

    def order(reference, order_supplier, lines):
        made = PurchaseOrder.objects.create(
            reference=reference,
            supplier=order_supplier,
            destination_warehouse=warehouse,
            order_date=date(2026, 9, 1),
        )
        for quantity, price in lines:
            PurchaseOrderLine.objects.create(
                purchase_order=made,
                variant=variant(f"{reference}-{quantity}"),
                quantity_ordered=quantity,
                unit_price=Decimal(price),
            )
        return made

    # 100 * 12.50 = 1250, plus 3 * 4.25 = 12.75, so three lines rather than one and a
    # value that a rounded-off decimal would get wrong.
    return {
        "two_lines": order("PO-1", supplier, [(100, "12.50"), (3, "4.25")]),
        "one_line": order("PO-2", supplier, [(10, "2.00")]),
        "no_lines": order("PO-3", other_supplier, []),
        # The second supplier's only order with a value, so a filter by supplier changes
        # the footer rather than happening to match it.
        "other_supplier": order("PO-4", other_supplier, [(2, "50.00")]),
    }


def list_orders(params=None):
    # Totals are opt-in, so every request here names the one it reads, the way the list
    # view does for a visible total column.
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=SUPERVISOR))
    return client.get(reverse("catalog.purchaseorder-list"), {"ct": "total_value", **(params or {})})


def values_by_reference(response):
    return {row["reference"]: row["total_value"] for row in response.data["results"]}


def test_each_order_carries_the_value_of_its_lines(orders):
    response = list_orders()

    assert response.status_code == 200, response.data
    assert values_by_reference(response) == {
        "PO-1": "1262.75",
        "PO-2": "20.00",
        "PO-3": "0.00",
        "PO-4": "100.00",
    }


def test_an_order_with_no_lines_is_worth_zero_rather_than_null(orders):
    """
    ``Coalesce`` in the annotation, not a client-side fallback. A null here would render
    as an empty cell in the list and would make the footer's sum of one empty page and one
    valueless order look the same.
    """
    response = list_orders({"reference": "PO-3"})

    assert values_by_reference(response) == {"PO-3": "0.00"}
    assert response.data["columnTotals"] == {"total_value": Decimal("0.00")}


def test_the_footer_totals_every_matching_order(orders):
    response = list_orders()

    assert response.data["columnTotals"] == {"total_value": Decimal("1382.75")}


def test_the_total_follows_the_filter_rather_than_the_page(orders):
    """
    VUEDA aggregates after filtering and before pagination, so a supplier filter reports
    what is owed to that supplier. This is the number a dashboard tile reads.
    """
    supplier_id = orders["two_lines"].supplier_id

    response = list_orders({"supplier": supplier_id, "ps": 1})

    assert len(response.data["results"]) == 1
    assert response.data["totalRecords"] == 2
    assert response.data["columnTotals"] == {"total_value": Decimal("1282.75")}


def test_a_multi_line_order_is_not_multiplied_by_its_own_lines(orders):
    """
    The annotation is a correlated subquery rather than a join. A joined ``Sum`` would fan
    each order out to one row per line, and the footer would count the two-line order
    twice, which is the failure this shape exists to avoid.
    """
    response = list_orders({"reference": "PO-1"})

    assert response.data["totalRecords"] == 1
    assert response.data["columnTotals"] == {"total_value": Decimal("1262.75")}


def test_a_created_order_reports_its_value_without_a_second_request(orders):
    """
    A write response serializes the instance the write returned, which no queryset
    annotated. The serializer computes it from the lines just saved instead, so the
    number the form lands on matches the number the list shows.
    """
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=SUPERVISOR))
    variant = WidgetVariant.objects.first()

    created = client.post(
        f"{reverse('catalog.purchaseorder-list')}?{EXPAND_PARAM}=lines",
        {
            "reference": "PO-NEW",
            "supplier": orders["two_lines"].supplier_id,
            "destination_warehouse": orders["two_lines"].destination_warehouse_id,
            "order_date": "2026-09-19",
            "lines": [{"variant": variant.id, "quantity_ordered": 4, "unit_price": "1.25"}],
        },
        format="json",
    )

    assert created.status_code == 201, created.data
    assert created.data["total_value"] == "5.00"
    assert values_by_reference(list_orders({"reference": "PO-NEW"})) == {"PO-NEW": "5.00"}


def test_the_detail_view_carries_the_value_too(orders):
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=SUPERVISOR))

    response = client.get(reverse("catalog.purchaseorder-detail", kwargs={"pk": orders["two_lines"].pk}))

    assert response.status_code == 200, response.data
    assert response.data["total_value"] == "1262.75"


def test_orders_sort_by_value_on_the_server(orders):
    """
    The annotation is a database expression, so ordering by it sorts every order rather
    than the page. ``total_value`` has to be in the viewset's ``ordering_fields`` for
    VUEDA to accept the parameter at all.
    """
    response = list_orders({ORDERING_PARAM: "-total_value"})

    assert response.status_code == 200, response.data

    assert [row["reference"] for row in response.data["results"]] == ["PO-1", "PO-4", "PO-2", "PO-3"]


def test_model_info_describes_the_annotated_column_as_a_decimal(orders):
    """
    The client builds a column from the metadata, so an annotation with no column behind it
    has to say what it is. ``get_field_model_info`` on the serializer is where that is said;
    without it the field reports null types, the column renders untyped, and
    ``manage.py check`` reports ``vueda_info.W001``.
    """
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=SUPERVISOR))
    url = reverse("info.model_info-detail", kwargs={"app_label": "catalog", "model": "purchaseorder"})

    response = client.get(f"{url}?{MODEL_INFO_QUERY}")

    assert response.status_code == 200, response.data
    total_value = response.data["model_fields"]["total_value"]
    assert total_value["type_db"] == "DecimalField"
    assert total_value["type_model"] == "DecimalField"
    assert total_value["read_only"]
