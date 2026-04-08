from django.urls import include, path

from widget_warehouse.catalog.routers import urlpatterns

urlpatterns = [
    path("", include(urlpatterns)),
]
