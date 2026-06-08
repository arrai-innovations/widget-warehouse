from vueda.core.fields.serializers import FileField, ImageField, RangeField
from vueda.core.serializers import VuedaLookupSerializer, VuedaSerializer

from widget_warehouse.catalog.models import (
    InventoryRecord,
    Promotion,
    Supplier,
    Warehouse,
    Widget,
    WidgetCategory,
    WidgetVariant,
)


class WidgetCategorySerializer(VuedaLookupSerializer):
    class Meta(VuedaLookupSerializer.Meta):
        model = WidgetCategory
        fields = (*VuedaLookupSerializer.Meta.fields, "description")


class SupplierSerializer(VuedaSerializer):
    class Meta(VuedaSerializer.Meta):
        model = Supplier
        fields = (
            "id",
            "name",
            "slug",
            "website",
            "contact_email",
            "country",
            "reliability_score",
            "typical_lead_days",
            "is_approved",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
            *VuedaSerializer.Meta.fields,
        )
        read_only_fields = ("created_at", "updated_at")


class WidgetSerializer(VuedaSerializer):
    image = ImageField(required=False, allow_null=True)
    datasheet = FileField(required=False, allow_null=True)

    class Meta(VuedaSerializer.Meta):
        model = Widget
        fields = (
            "id",
            "name",
            "slug",
            "sku",
            "category",
            "supplier",
            "description",
            "unit_price",
            "weight_kg",
            "warranty_period",
            "is_active",
            "release_date",
            "image",
            "datasheet",
            "specifications",
            "created_at",
            "updated_at",
            *VuedaSerializer.Meta.fields,
        )
        read_only_fields = ("created_at", "updated_at")


class WidgetVariantSerializer(VuedaSerializer):
    class Meta(VuedaSerializer.Meta):
        model = WidgetVariant
        fields = (
            "id",
            "widget",
            "name",
            "sku_suffix",
            "additional_price",
            "stock_quantity",
            *VuedaSerializer.Meta.fields,
        )


class WarehouseSerializer(VuedaSerializer):
    class Meta(VuedaSerializer.Meta):
        model = Warehouse
        fields = (
            "id",
            "name",
            "code",
            "uuid",
            "address",
            "contact_email",
            "opens_at",
            "closes_at",
            "is_active",
            *VuedaSerializer.Meta.fields,
        )
        read_only_fields = ("uuid",)


class InventoryRecordSerializer(VuedaSerializer):
    class Meta(VuedaSerializer.Meta):
        model = InventoryRecord
        fields = (
            "id",
            "variant",
            "warehouse",
            "quantity_on_hand",
            "reorder_threshold",
            "max_stock_level",
            "last_stocktake_at",
            "last_received_at",
            "notes",
            "available_actions",
        )


class PromotionSerializer(VuedaSerializer):
    valid_dates = RangeField()

    class Meta(VuedaSerializer.Meta):
        model = Promotion
        fields = (
            "id",
            "name",
            "code",
            "description",
            "discount_percent",
            "valid_dates",
            "is_active",
            "widgets",
            "created_at",
            *VuedaSerializer.Meta.fields,
        )
        read_only_fields = ("created_at",)
