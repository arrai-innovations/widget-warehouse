from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "widget_warehouse.catalog"

    def ready(self):
        from vueda.info import register

        from .serializers import (
            InventoryRecordSerializer,
            PromotionSerializer,
            PurchaseOrderSerializer,
            SupplierSerializer,
            WarehouseSerializer,
            WidgetCategorySerializer,
            WidgetSerializer,
            WidgetVariantSerializer,
        )
        from .viewsets import (
            InventoryRecordViewSet,
            PromotionViewSet,
            PurchaseOrderViewSet,
            SupplierViewSet,
            WarehouseViewSet,
            WidgetCategoryViewSet,
            WidgetVariantViewSet,
            WidgetViewSet,
        )

        register(InventoryRecordSerializer, InventoryRecordViewSet)
        register(PromotionSerializer, PromotionViewSet)
        register(PurchaseOrderSerializer, PurchaseOrderViewSet)
        register(SupplierSerializer, SupplierViewSet)
        register(WarehouseSerializer, WarehouseViewSet)
        register(WidgetCategorySerializer, WidgetCategoryViewSet)
        register(WidgetSerializer, WidgetViewSet)
        register(WidgetVariantSerializer, WidgetVariantViewSet)
