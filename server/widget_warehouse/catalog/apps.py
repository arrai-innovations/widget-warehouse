from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "widget_warehouse.catalog"

    def ready(self):
        from vueda.info import register

        from .serializers import (
            WidgetCategorySerializer,
            WidgetSerializer,
            WidgetVariantSerializer,
        )
        from .viewsets import (
            WidgetCategoryViewSet,
            WidgetVariantViewSet,
            WidgetViewSet,
        )

        register(WidgetCategorySerializer, WidgetCategoryViewSet)
        register(WidgetSerializer, WidgetViewSet)
        register(WidgetVariantSerializer, WidgetVariantViewSet)
