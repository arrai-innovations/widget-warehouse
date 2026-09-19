from typing import ClassVar

from django.conf import settings
from vueda.core.fields.serializers import FileField, ImageField, RangeField
from vueda.core.serializers import VuedaLookupSerializer, VuedaSerializer
from vueda.workflow.serializers import HasWorkflowSerializerMixin

from widget_warehouse.catalog.models import (
    InventoryRecord,
    Promotion,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStateCount,
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
            "notification_emails",
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
        expandable_fields: ClassVar[dict] = {
            "category": (
                WidgetCategorySerializer,
                {
                    settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ("id", "formatted_name"),
                },
            ),
            "supplier": (
                SupplierSerializer,
                {
                    settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ("id", "formatted_name"),
                },
            ),
        }
        expandable_fields.update(VuedaSerializer.Meta.expandable_fields)


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
        expandable_fields: ClassVar[dict] = {
            "widget": (
                WidgetSerializer,
                {
                    settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ("id", "formatted_name"),
                },
            ),
        }
        expandable_fields.update(VuedaSerializer.Meta.expandable_fields)


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
        expandable_fields: ClassVar[dict] = {
            "variant": (
                WidgetVariantSerializer,
                {
                    settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ("id", "formatted_name"),
                },
            ),
            "warehouse": (
                WarehouseSerializer,
                {
                    settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ("id", "formatted_name"),
                },
            ),
        }
        expandable_fields.update(VuedaSerializer.Meta.expandable_fields)


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


class PurchaseOrderLineSerializer(VuedaSerializer):
    """
    Child serializer for the purchase order's writable inline.

    ``purchase_order`` is deliberately absent: the parent sets the foreign key when it
    saves its own lines, and a required parent field could never be satisfied on create.
    Lines are therefore only reachable through ``PurchaseOrderSerializer``.
    """

    class Meta(VuedaSerializer.Meta):
        model = PurchaseOrderLine
        # No formatted_name: it would render as a second, read-only variant column beside
        # the variant picker in the inline, which is the same value twice.
        fields = (
            "id",
            "variant",
            "quantity_ordered",
            "unit_price",
            "available_actions",
        )
        expandable_fields: ClassVar[dict] = {
            "variant": (
                WidgetVariantSerializer,
                {
                    settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ("id", "formatted_name"),
                },
            ),
        }
        expandable_fields.update(VuedaSerializer.Meta.expandable_fields)


class PurchaseOrderSerializer(HasWorkflowSerializerMixin, VuedaSerializer):
    """
    Read/write serializer for the order and its lines.

    ``HasWorkflowSerializerMixin`` adds the current state and the transitions this
    request's user may run on this row, so a list response carries both the state to
    display and the affordances to offer without a second call per row.
    """

    class Meta(VuedaSerializer.Meta):
        model = PurchaseOrder
        fields = (
            "id",
            "reference",
            "supplier",
            "destination_warehouse",
            "order_date",
            "expected_arrival_date",
            "lines",
            "created_at",
            "updated_at",
            *VuedaSerializer.Meta.fields,
            *HasWorkflowSerializerMixin.Meta.fields,
        )
        read_only_fields = ("created_at", "updated_at")
        expandable_fields: ClassVar[dict] = {
            "supplier": (
                SupplierSerializer,
                {
                    settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ("id", "formatted_name"),
                },
            ),
            "destination_warehouse": (
                WarehouseSerializer,
                {
                    settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ("id", "formatted_name"),
                },
            ),
            # Writable inline. Expanding "lines" on a write request is what makes the
            # nested payload deserialize as objects rather than primary keys, and an
            # existing line left out of that payload is deleted.
            "lines": (PurchaseOrderLineSerializer, {"many": True}),
        }
        expandable_fields.update(VuedaSerializer.Meta.expandable_fields)


class PurchaseOrderStateCountSerializer(VuedaSerializer):
    """
    Read-only by construction: the model is backed by a view over an aggregate, so there is
    nothing to write back to. Every field is listed in ``read_only_fields`` rather than the
    viewset simply refusing writes, so the refusal shows up in model info and the client
    never offers a create or update form for it.
    """

    class Meta(VuedaSerializer.Meta):
        model = PurchaseOrderStateCount
        fields = (
            "id",
            "state",
            "code",
            "name",
            "position",
            "order_count",
            # Not *VuedaSerializer.Meta.fields. A view cannot carry the stored
            # formatted_name column, and object_revision needs a history table this model
            # does not have, so listing them would serialize two permanent nulls.
            # InventoryRecord, which also opts out of formatted_name, names the one field
            # it wants the same way.
            "available_actions",
        )
        read_only_fields = ("id", "state", "code", "name", "position", "order_count")
