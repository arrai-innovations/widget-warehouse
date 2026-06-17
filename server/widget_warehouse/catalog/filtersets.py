from django_filters import rest_framework
from vueda.core.filters import VuedaFilterSet

from widget_warehouse.catalog.models import (
    InventoryRecord,
    Promotion,
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

    class Meta:
        model = Widget
        fields = ("id", "name", "slug", "sku", "category", "supplier", "is_active")


class WidgetVariantFilterSet(VuedaFilterSet):
    class Meta:
        model = WidgetVariant
        fields = ("id", "widget", "name")


class WarehouseFilterSet(VuedaFilterSet):
    class Meta:
        model = Warehouse
        fields = ("id", "name", "code", "is_active")


class InventoryRecordFilterSet(VuedaFilterSet):
    class Meta:
        model = InventoryRecord
        fields = ("id", "variant", "warehouse")


class PromotionFilterSet(VuedaFilterSet):
    class Meta:
        model = Promotion
        fields = ("id", "name", "code", "is_active")
