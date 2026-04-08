from vueda.core.routers import VuedaRouter

from widget_warehouse.catalog.viewsets import (
    WidgetCategoryViewSet,
    WidgetVariantViewSet,
    WidgetViewSet,
)

router = VuedaRouter()
router.register(r"widgets", WidgetViewSet)
router.register(r"widget-categories", WidgetCategoryViewSet)
router.register(r"widget-variants", WidgetVariantViewSet)
urlpatterns = router.urls
