from vueda.core.serializers import VuedaLookupSerializer, VuedaSerializer

from widget_warehouse.catalog.models import Widget, WidgetCategory, WidgetVariant


class WidgetCategorySerializer(VuedaLookupSerializer):
    class Meta(VuedaLookupSerializer.Meta):
        model = WidgetCategory
        fields = [*VuedaLookupSerializer.Meta.fields, "description"]


class WidgetSerializer(VuedaSerializer):
    class Meta(VuedaSerializer.Meta):
        model = Widget
        fields = [
            "id",
            "name",
            "sku",
            "category",
            "description",
            "unit_price",
            "weight_kg",
            "is_active",
            "release_date",
            "created_at",
            "updated_at",
            "formatted_name",
            "available_actions",
        ]
        read_only_fields = ["created_at", "updated_at"]


class WidgetVariantSerializer(VuedaSerializer):
    class Meta(VuedaSerializer.Meta):
        model = WidgetVariant
        fields = [
            "id",
            "widget",
            "name",
            "sku_suffix",
            "additional_price",
            "stock_quantity",
            "formatted_name",
            "available_actions",
        ]
