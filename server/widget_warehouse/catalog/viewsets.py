from typing import ClassVar

from vueda.core.viewsets import VuedaViewSet

from widget_warehouse.catalog.filtersets import (
    InventoryRecordFilterSet,
    PromotionFilterSet,
    PurchaseOrderFilterSet,
    SupplierFilterSet,
    WarehouseFilterSet,
    WidgetCategoryFilterSet,
    WidgetFilterSet,
    WidgetVariantFilterSet,
)
from widget_warehouse.catalog.models import (
    InventoryRecord,
    Promotion,
    PurchaseOrder,
    Supplier,
    Warehouse,
    Widget,
    WidgetCategory,
    WidgetVariant,
)
from widget_warehouse.catalog.serializers import (
    InventoryRecordSerializer,
    PromotionSerializer,
    PurchaseOrderSerializer,
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
    ordering_fields: ClassVar[list[str]] = [
        "name",
        "slug",
        "sku",
        "category",
        "supplier",
        "unit_price",
        "weight_kg",
        "warranty_period",
        "is_active",
        "release_date",
        "created_at",
        "updated_at",
    ]
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


class PurchaseOrderViewSet(VuedaViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filterset_class = PurchaseOrderFilterSet
    # "lines" is here so a list request can expand the inline as well: without it,
    # flex-fields refuses the expand on list and the create/update forms are the only
    # place the child rows are reachable.
    permit_list_expands: ClassVar[list[str]] = ["supplier", "destination_warehouse", "lines"]
    ordering_fields: ClassVar[list[str]] = [
        "reference",
        "supplier",
        "destination_warehouse",
        "order_date",
        "expected_arrival_date",
        "created_at",
        "updated_at",
    ]
    search_fields: ClassVar[list[str]] = [
        "reference",
        "supplier__name",
        "supplier__slug",
        "destination_warehouse__code",
        "destination_warehouse__name",
    ]
