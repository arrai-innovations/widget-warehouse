from vueda.core.routers import VuedaRouter

from widget_warehouse.catalog.viewsets import (
    WidgetCategoryViewSet,
    WidgetVariantViewSet,
    WidgetViewSet,
)

router = VuedaRouter()
router.register(r"widget", WidgetViewSet)
router.register(r"widgetcategory", WidgetCategoryViewSet)
router.register(r"widgetvariant", WidgetVariantViewSet)
urlpatterns = router.urls
