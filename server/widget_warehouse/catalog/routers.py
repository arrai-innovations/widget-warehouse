from vueda.core.routers import VuedaRouter

from widget_warehouse.catalog.viewsets import (
    InventoryRecordViewSet,
    PromotionViewSet,
    PurchaseOrderStateCountViewSet,
    PurchaseOrderViewSet,
    SupplierPriceViewSet,
    SupplierViewSet,
    WarehouseViewSet,
    WidgetCategoryViewSet,
    WidgetVariantViewSet,
    WidgetViewSet,
)

router = VuedaRouter()
router.register(r"supplier", SupplierViewSet)
router.register(r"widget", WidgetViewSet)
router.register(r"widgetcategory", WidgetCategoryViewSet)
router.register(r"widgetvariant", WidgetVariantViewSet)
router.register(r"warehouse", WarehouseViewSet)
router.register(r"inventoryrecord", InventoryRecordViewSet)
router.register(r"promotion", PromotionViewSet)
router.register(r"purchaseorder", PurchaseOrderViewSet)
router.register(r"purchaseorderstatecount", PurchaseOrderStateCountViewSet)
router.register(r"supplierprice", SupplierPriceViewSet)
urlpatterns = router.urls
