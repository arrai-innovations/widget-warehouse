from vueda.core.filters import VuedaFilterSet

from widget_warehouse.catalog.models import Widget, WidgetCategory, WidgetVariant


class WidgetCategoryFilterSet(VuedaFilterSet):
    class Meta:
        model = WidgetCategory
        fields = ["id", "code", "name"]


class WidgetFilterSet(VuedaFilterSet):
    class Meta:
        model = Widget
        fields = ["id", "name", "sku", "category", "is_active"]


class WidgetVariantFilterSet(VuedaFilterSet):
    class Meta:
        model = WidgetVariant
        fields = ["id", "widget", "name"]
