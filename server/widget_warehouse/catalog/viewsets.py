from typing import ClassVar

from vueda.core.viewsets import VuedaViewSet

from widget_warehouse.catalog.filtersets import (
    InventoryRecordFilterSet,
    PromotionFilterSet,
    SupplierFilterSet,
    WarehouseFilterSet,
    WidgetCategoryFilterSet,
    WidgetFilterSet,
    WidgetVariantFilterSet,
)
from widget_warehouse.catalog.models import (
    InventoryRecord,
    Promotion,
    Supplier,
    Warehouse,
    Widget,
    WidgetCategory,
    WidgetVariant,
)
from widget_warehouse.catalog.serializers import (
    InventoryRecordSerializer,
    PromotionSerializer,
    SupplierSerializer,
    WarehouseSerializer,
    WidgetCategorySerializer,
    WidgetSerializer,
    WidgetVariantSerializer,
)


class WidgetCategoryViewSet(VuedaViewSet):
    queryset = WidgetCategory.objects.all()
    serializer_class = WidgetCategorySerializer
    filterset_class = WidgetCategoryFilterSet


class SupplierViewSet(VuedaViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_class = SupplierFilterSet


class WidgetViewSet(VuedaViewSet):
    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer
    filterset_class = WidgetFilterSet
    permit_list_expands: ClassVar[list[str]] = ["category", "supplier"]
    search_fields: ClassVar[list[str]] = [
        "name",
        "slug",
        "sku",
        "description",
        "category__code",
        "category__name",
        "supplier__name",
        "supplier__slug",
    ]


class WidgetVariantViewSet(VuedaViewSet):
    queryset = WidgetVariant.objects.all()
    serializer_class = WidgetVariantSerializer
    filterset_class = WidgetVariantFilterSet


class WarehouseViewSet(VuedaViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    filterset_class = WarehouseFilterSet


class InventoryRecordViewSet(VuedaViewSet):
    queryset = InventoryRecord.objects.all()
    serializer_class = InventoryRecordSerializer
    filterset_class = InventoryRecordFilterSet


class PromotionViewSet(VuedaViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    filterset_class = PromotionFilterSet
