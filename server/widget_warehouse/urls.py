from django.urls import include, path

urlpatterns = [
    path("catalog/", include("widget_warehouse.catalog.urls")),
]
