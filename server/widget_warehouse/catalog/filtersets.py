from django.db.models import F, Q
from django_filters import rest_framework
from vueda.core.filters import VuedaFilterSet
from vueda.workflow.filtersets import HasWorkflowFilterSetMixin

from widget_warehouse.catalog.models import (
    InventoryRecord,
    Promotion,
    PurchaseOrder,
    PurchaseOrderStateCount,
    Supplier,
    Warehouse,
    Widget,
    WidgetCategory,
    WidgetVariant,
)


class WidgetCategoryFilterSet(VuedaFilterSet):
    class Meta:
        model = WidgetCategory
        fields = ("id", "code", "name")


class SupplierFilterSet(VuedaFilterSet):
    class Meta:
        model = Supplier
        fields = ("id", "name", "slug", "country", "is_approved", "is_active")


class WidgetFilterSet(VuedaFilterSet):
    name = rest_framework.CharFilter(field_name="name", label="Name", lookup_expr="icontains")
    slug = rest_framework.CharFilter(field_name="slug", label="Slug", lookup_expr="icontains")
    sku = rest_framework.CharFilter(field_name="sku", label="SKU", lookup_expr="icontains")
    sku_exact = rest_framework.CharFilter(field_name="sku", label="SKU exact", lookup_expr="iexact")
    unit_price = rest_framework.RangeFilter(field_name="unit_price", label="Unit price")
    weight_kg = rest_framework.RangeFilter(field_name="weight_kg", label="Weight (kg)")

    class Meta:
        model = Widget
        fields = ("id", "name", "slug", "sku", "category", "supplier", "unit_price", "weight_kg", "is_active")


class WidgetVariantFilterSet(VuedaFilterSet):
    class Meta:
        model = WidgetVariant
        fields = ("id", "widget", "name")


class WarehouseFilterSet(VuedaFilterSet):
    class Meta:
        model = Warehouse
        fields = ("id", "name", "code", "is_active")


class InventoryRecordFilterSet(VuedaFilterSet):
    """
    ``below_reorder`` compares two columns of the same row, which no generated filter can
    express: the threshold is per record, not a value a request supplies. A
    ``BooleanFilter`` with a method is the hook for that, and because it is a declared
    filter VUEDA reports it in model info like any other, so the client renders it without
    knowing it is special.
    """

    below_reorder = rest_framework.BooleanFilter(
        method="filter_below_reorder",
        label="Below reorder threshold",
    )
    quantity_on_hand = rest_framework.RangeFilter(field_name="quantity_on_hand", label="Quantity on hand")

    def filter_below_reorder(self, queryset, name, value):
        if value is None:
            return queryset
        predicate = Q(quantity_on_hand__lt=F("reorder_threshold"))
        return queryset.filter(predicate) if value else queryset.exclude(predicate)

    class Meta:
        model = InventoryRecord
        fields = ("id", "variant", "warehouse", "quantity_on_hand", "below_reorder")


class PromotionFilterSet(VuedaFilterSet):
    class Meta:
        model = Promotion
        fields = ("id", "name", "code", "is_active")


class PurchaseOrderFilterSet(HasWorkflowFilterSetMixin, VuedaFilterSet):
    """
    ``HasWorkflowFilterSetMixin`` contributes the ``workflow_state`` filter, which is how a
    list request narrows to orders in a given state. The mixin narrows its own choices to
    the states orders are actually in, so the filter's options describe this queryset
    rather than every state the workflow defines.
    """

    reference = rest_framework.CharFilter(field_name="reference", label="Reference", lookup_expr="icontains")
    order_date = rest_framework.DateFromToRangeFilter(field_name="order_date", label="Order date")
    expected_arrival_date = rest_framework.DateFromToRangeFilter(
        field_name="expected_arrival_date",
        label="Expected arrival",
    )

    class Meta:
        model = PurchaseOrder
        fields = ("id", "reference", "supplier", "destination_warehouse", "order_date", "expected_arrival_date")


class PurchaseOrderStateCountFilterSet(VuedaFilterSet):
    class Meta:
        model = PurchaseOrderStateCount
        fields = ("id", "code")
