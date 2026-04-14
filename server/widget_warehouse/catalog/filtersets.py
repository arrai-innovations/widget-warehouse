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
        fields = ["id", "code", "name"]


class SupplierFilterSet(VuedaFilterSet):
    class Meta:
        model = Supplier
        fields = ["id", "name", "slug", "country", "is_approved", "is_active"]


class WidgetFilterSet(VuedaFilterSet):
    class Meta:
        model = Widget
        fields = ["id", "name", "sku", "category", "supplier", "is_active"]


class WidgetVariantFilterSet(VuedaFilterSet):
    class Meta:
        model = WidgetVariant
        fields = ["id", "widget", "name"]


class WarehouseFilterSet(VuedaFilterSet):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "code", "is_active"]


class InventoryRecordFilterSet(VuedaFilterSet):
    class Meta:
        model = InventoryRecord
        fields = ["id", "variant", "warehouse"]


class PromotionFilterSet(VuedaFilterSet):
    class Meta:
        model = Promotion
        fields = ["id", "name", "code", "is_active"]
