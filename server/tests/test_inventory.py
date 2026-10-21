"""
Contract tests for the inventory list's filters and its server-side totals.

``below_reorder`` is the project's one column-to-column filter: it compares a row's stock
against that row's own threshold rather than against a value the request supplies. It
exists so an operator (and, later, a dashboard tile) can ask "what needs restocking"
without knowing any thresholds, so the boundary cases are pinned here.

The totals come from VUEDA's ``column_totals``, which a request asks for with ``ct`` and
which sums over the filtered queryset rather than the page, so the two features are tested together: a total that ignored the
filter would be worse than no total at all.
"""

from urllib.parse import urlencode

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory
from vueda.core.filters import VuedaSearchFilterBackend

from widget_warehouse.catalog.filtersets import InventoryRecordFilterSet
from widget_warehouse.catalog.models import (
    InventoryRecord,
    Supplier,
    Warehouse,
    Widget,
    WidgetCategory,
    WidgetVariant,
)
from widget_warehouse.catalog.seeding import DemoUsers
from widget_warehouse.catalog.serializers import InventoryRecordSerializer
from widget_warehouse.catalog.viewsets import InventoryRecordViewSet


@pytest.fixture
def stock(db):
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
        supplier=Supplier.objects.create(
            name="Precision Parts Co.",
            slug="precision-parts-co",
            contact_email="sales@example.com",
        ),
        unit_price="12.50",
    )

    def record(suffix, on_hand, threshold):
        variant = WidgetVariant.objects.create(widget=widget, name=suffix, sku_suffix=suffix)
        return InventoryRecord.objects.create(
            variant=variant,
            warehouse=warehouse,
            quantity_on_hand=on_hand,
            reorder_threshold=threshold,
        )

    return {
        "short": record("SM", on_hand=2, threshold=10),
        "exactly_at": record("MD", on_hand=10, threshold=10),
        "healthy": record("LG", on_hand=50, threshold=10),
        "no_threshold": record("XL", on_hand=0, threshold=0),
    }


def filtered_ids(params):
    return set(InventoryRecordFilterSet(params, queryset=InventoryRecord.objects.all()).qs.values_list("id", flat=True))


@pytest.mark.django_db
def test_below_reorder_selects_only_records_under_their_own_threshold(stock):
    assert filtered_ids({"below_reorder": "true"}) == {stock["short"].id}


@pytest.mark.django_db
def test_a_record_sitting_exactly_on_its_threshold_is_not_below_it(stock):
    # The threshold reads "reorder when it falls below this level", so equal is still fine.
    assert stock["exactly_at"].id not in filtered_ids({"below_reorder": "true"})


@pytest.mark.django_db
def test_a_zero_threshold_never_reports_as_short(stock):
    # quantity_on_hand is a positive integer field, so nothing can sit under a zero
    # threshold. A record with no threshold set should never appear in a restock queue.
    assert stock["no_threshold"].id not in filtered_ids({"below_reorder": "true"})


@pytest.mark.django_db
def test_below_reorder_false_returns_the_complement(stock):
    healthy = {stock["exactly_at"].id, stock["healthy"].id, stock["no_threshold"].id}

    assert filtered_ids({"below_reorder": "false"}) == healthy


@pytest.mark.django_db
def test_an_absent_below_reorder_leaves_the_queryset_alone(stock):
    assert filtered_ids({}) == {record.id for record in stock.values()}


@pytest.mark.django_db
def test_quantity_on_hand_filters_by_range(stock):
    assert filtered_ids({"quantity_on_hand_min": "10", "quantity_on_hand_max": "50"}) == {
        stock["exactly_at"].id,
        stock["healthy"].id,
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("term", "expected"),
    [
        ("SPR-100-SM @ SYD-DC", {"short"}),
        ('"SPR-100-SM @ SYD-DC"', {"short"}),
        ("spr-100-sm", {"short"}),
        ("SM SYD-DC", {"short"}),
        ("SYD-DC", {"short", "exactly_at", "healthy", "no_threshold"}),
        ("SPR-100-SM @ MEL-OVF", set()),
        ("nonexistent-stock-item", set()),
    ],
)
def test_stock_item_search(stock, settings, term, expected):
    request = Request(APIRequestFactory().get("/", {settings.REST_FRAMEWORK["SEARCH_PARAM"]: term}))
    view = InventoryRecordViewSet()
    queryset = VuedaSearchFilterBackend().filter_queryset(request, view.queryset.all(), view)

    assert set(queryset.values_list("id", flat=True)) == {stock[name].id for name in expected}
    assert all(record.stock_item_search == record.get_formatted_name() for record in queryset)


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["product_active", "warehouse_active", "supplier_active", "supplier_approved"])
def test_inventory_status_filters_follow_related_records(stock, field):
    record = stock["short"]
    related, attribute = {
        "product_active": (record.variant.widget, "is_active"),
        "warehouse_active": (record.warehouse, "is_active"),
        "supplier_active": (record.variant.widget.supplier, "is_active"),
        "supplier_approved": (record.variant.widget.supplier, "is_approved"),
    }[field]
    all_ids = {item.id for item in stock.values()}
    for value in (True, False):
        setattr(related, attribute, value)
        related.save()
        assert filtered_ids({field: str(value).lower()}) == all_ids
        assert filtered_ids({field: str(not value).lower()}) == set()
        assert filtered_ids({}) == all_ids
        assert InventoryRecordSerializer(InventoryRecordViewSet.queryset.get(pk=record.pk)).data[field] is value


@pytest.mark.django_db
def test_inventory_supplier_status_preserves_unknown_and_missing_supplier(stock):
    record = stock["short"]
    supplier = record.variant.widget.supplier
    supplier.is_approved = None
    supplier.save()
    data = InventoryRecordSerializer(InventoryRecordViewSet.queryset.get(pk=record.pk)).data
    assert data["supplier_approved"] is None
    assert filtered_ids({"supplier_approved": "true"}) == set()
    assert filtered_ids({"supplier_approved": "false"}) == set()

    widget = record.variant.widget
    widget.supplier = None
    widget.save()
    data = InventoryRecordSerializer(InventoryRecordViewSet.queryset.get(pk=record.pk)).data
    assert data["supplier_active"] is None
    assert data["supplier_approved"] is None
    assert filtered_ids({"supplier_active": "true", "supplier_approved": "true"}) == set()


@pytest.fixture
def seeded_roles(db):
    DemoUsers().run()


def list_as(email, query=""):
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=email))
    return client.get(f"{reverse('catalog.inventoryrecord-list')}{query}")


@pytest.mark.django_db
def test_inventory_search_combines_with_status_filters_and_totals(stock, seeded_roles):
    supplier = stock["short"].variant.widget.supplier
    supplier.is_active = True
    supplier.is_approved = True
    supplier.save()
    params = {
        "s": "SPR-100-SM @ SYD-DC",
        "product_active": "true",
        "warehouse_active": "true",
        "supplier_active": "true",
        "supplier_approved": "true",
        "ct": "quantity_on_hand",
    }
    response = list_as("clerk@widgetwarehouse.com", f"?{urlencode(params)}")
    assert response.status_code == 200, response.data
    assert response.data["totalRecords"] == 1
    assert response.data["columnTotals"] == {"quantity_on_hand": 2}
    row = response.data["results"][0]
    assert row["formatted_name"] == params["s"]
    for field in ("product_active", "warehouse_active", "supplier_active", "supplier_approved"):
        assert row[field] is True

    params["s"] = "nonexistent-stock-item"
    response = list_as("clerk@widgetwarehouse.com", f"?{urlencode(params)}")
    assert response.status_code == 200, response.data
    assert response.data["totalRecords"] == 0
    assert response.data["columnTotals"] == {"quantity_on_hand": 0}

    params["s"] = "SPR-100-SM @ SYD-DC"
    params["supplier_approved"] = "false"
    response = list_as("clerk@widgetwarehouse.com", f"?{urlencode(params)}")
    assert response.status_code == 200, response.data
    assert response.data["totalRecords"] == 0


@pytest.mark.django_db
def test_inventory_status_metadata_offers_read_only_columns_and_boolean_filters(seeded_roles):
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email="clerk@widgetwarehouse.com"))
    response = client.get("/routes/vueda.info/model_info/catalog/inventoryrecord/?e=model_fields,model_filtering")

    assert response.status_code == 200, response.data
    for name in ("product_active", "warehouse_active", "supplier_active", "supplier_approved"):
        field = response.data["model_fields"][name]
        assert field["type_model"] == "BooleanField"
        assert field["read_only"] is True
        filter_info = response.data["model_filtering"][name]
        assert filter_info["hidden"] is False
        assert filter_info["label"] == field["label"]
        assert filter_info["choices"] == [{"label": "Yes", "value": "true"}, {"label": "No", "value": "false"}]


@pytest.mark.django_db
def test_the_list_carries_a_total_for_every_matching_row(stock, seeded_roles):
    response = list_as("clerk@widgetwarehouse.com", "?ct=quantity_on_hand")

    assert response.status_code == 200, response.data
    # 2 + 10 + 50 + 0, every record in the fixture rather than the page.
    assert response.data["columnTotals"] == {"quantity_on_hand": 62}


@pytest.mark.django_db
def test_the_total_follows_the_filter(stock, seeded_roles):
    response = list_as("clerk@widgetwarehouse.com", "?below_reorder=true&ct=quantity_on_hand")

    assert response.status_code == 200, response.data
    assert response.data["totalRecords"] == 1
    assert response.data["columnTotals"] == {"quantity_on_hand": 2}


@pytest.mark.django_db
def test_a_total_over_no_rows_is_zero(stock, seeded_roles):
    """
    ``Sum`` over an empty queryset is NULL in SQL, and VUEDA totals it as zero instead, so
    the footer shows 0 for a filter that matches nothing rather than an empty cell.
    """
    response = list_as("clerk@widgetwarehouse.com", "?quantity_on_hand_min=9000&ct=quantity_on_hand")

    assert response.status_code == 200, response.data
    assert response.data["totalRecords"] == 0
    assert response.data["columnTotals"] == {"quantity_on_hand": 0}


@pytest.mark.django_db
def test_a_record_names_itself_by_sku_and_warehouse(stock, seeded_roles):
    """
    ``InventoryRecord`` computes ``formatted_name`` in Python rather than carrying it as a
    stored column, because the name reaches through two relations and a generated column
    cannot leave its own row.

    That is also why the serializer redeclares the field. ``VuedaSerializer`` serves
    ``formatted_name`` as a ``ReadOnlyField``, which reads the attribute of that name off
    the instance; this model sets that attribute to ``None`` and answers through
    ``get_formatted_name()`` instead, so the read-only field would serialize null for
    every row, quietly and forever. This pins the value rather than the mechanism, so it
    fails whichever way the wiring is lost.
    """
    response = list_as("clerk@widgetwarehouse.com", "?below_reorder=true")

    assert response.status_code == 200, response.data
    assert [row["formatted_name"] for row in response.data["results"]] == ["SPR-100-SM @ SYD-DC"]


@pytest.mark.django_db
def test_inventory_edits_are_offered_and_enforced_only_for_supervisors(stock, seeded_roles):
    record = stock["short"]
    detail_url = reverse("catalog.inventoryrecord-detail", args=[record.pk])
    for name in ("supervisor", "clerk", "associate", "manager", "accountant"):
        client = APIClient()
        client.force_authenticate(get_user_model().objects.get(email=f"{name}@widgetwarehouse.com"))
        info = client.get("/routes/vueda.info/model_info/catalog/inventoryrecord/?e=model_actions")
        assert info.status_code == 200, info.data
        actions = {action["name"] for action in info.data["model_actions"]}
        assert ("update" in actions) == (name == "supervisor")
        assert "create" not in actions
        assert "delete" not in actions
        response = client.patch(detail_url, {"reorder_threshold": 20}, format="json")
        assert response.status_code == (200 if name == "supervisor" else 403), response.data
        denied = client.delete(detail_url)
        assert denied.status_code == 403, denied.data
        denied = client.post(
            reverse("catalog.inventoryrecord-list"),
            {"variant": stock["healthy"].variant_id, "warehouse": record.warehouse_id},
            format="json",
        )
        assert denied.status_code == 403, denied.data


@pytest.mark.django_db
def test_naming_a_record_costs_no_extra_query_per_row(stock, seeded_roles):
    """
    The name reaches ``variant.widget.sku`` and ``warehouse.code``, which is three tables
    away from the row. ``formatted_name_select_related`` on the model is what keeps that
    from becoming a query per row, and it belongs on the model rather than the viewset so
    a management command or a lookup's choices get it too.
    """
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    with CaptureQueriesContext(connection) as queries:
        names = [record.get_formatted_name() for record in InventoryRecord.objects.all()]

    assert len(names) == 4
    # One for the records; anything more means the relations were not pre-fetched.
    assert len(queries) == 1, [query["sql"] for query in queries]
