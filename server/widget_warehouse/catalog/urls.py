from django.urls import include, path

from widget_warehouse.catalog.purchasing import OrderPipelineViewSet, PurchasingTrendViewSet
from widget_warehouse.catalog.routers import urlpatterns

urlpatterns = [
    path("purchaseorder/pipeline/", OrderPipelineViewSet.as_view({"get": "list"}), name="catalog.order-pipeline"),
    path(
        "purchaseorder/purchasing_trend/",
        PurchasingTrendViewSet.as_view({"get": "list"}),
        name="catalog.purchasing-trend",
    ),
    path("", include(urlpatterns)),
]
