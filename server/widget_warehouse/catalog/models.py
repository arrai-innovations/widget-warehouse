import uuid
from decimal import Decimal

from django.contrib.postgres import fields as pg_fields
from django.db import models
from django.db.models.functions import Coalesce
from vueda.core.models import BaseModelMeta, FormattedNameManager, Lookup, VuedaModel
from vueda.workflow.models import HasWorkflowModelMixin

# The money an order is worth is a sum over its lines, so it is neither a column nor a
# GeneratedField: it is an annotation the viewset adds, a serializer field that reads it,
# and the column VUEDA's ``column_totals`` sums for the list footer. One output field is
# shared by the subquery, the annotation, and the serializer so the three agree on
# precision rather than each guessing.
TOTAL_VALUE_MAX_DIGITS = 12
TOTAL_VALUE_DECIMAL_PLACES = 2


def total_value_output_field():
    return models.DecimalField(max_digits=TOTAL_VALUE_MAX_DIGITS, decimal_places=TOTAL_VALUE_DECIMAL_PLACES)


class WidgetCategory(Lookup):
    """Type of widget: sprocket, gear, fastener, etc."""

    description = models.TextField(blank=True)

    class Meta(BaseModelMeta):
        ordering = ("name", "id")
        verbose_name_plural = "widget categories"


class Supplier(VuedaModel):
    """A company that supplies widgets to the warehouse."""

    COUNTRY_CHOICES = (
        ("AU", "Australia"),
        ("CN", "China"),
        ("DE", "Germany"),
        ("GB", "United Kingdom"),
        ("JP", "Japan"),
        ("TW", "Taiwan"),
        ("US", "United States"),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    website = models.URLField(blank=True)
    contact_email = models.EmailField()
    notification_emails = pg_fields.ArrayField(
        models.EmailField(),
        default=list,
        blank=True,
        help_text="Additional addresses copied on purchase orders sent to this supplier.",
    )
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, blank=True)
    reliability_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Supplier reliability rating from 0.0 to 5.0.",
    )
    typical_lead_days = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Typical lead time from order to delivery, in days.",
    )
    is_approved = models.BooleanField(
        null=True,
        blank=True,
        help_text="Approval status: null = under review, true = approved, false = rejected.",
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(BaseModelMeta):
        ordering = ("name", "id")


class Widget(VuedaModel):
    """A hypothetical manufactured product."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)
    sku = models.CharField("SKU", max_length=64, unique=True)
    category = models.ForeignKey(
        WidgetCategory,
        on_delete=models.PROTECT,
        related_name="widgets",
    )
    supplier = models.ForeignKey(
        Supplier,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="widgets",
    )
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    weight_kg = models.DecimalField("Weight (kg)", max_digits=8, decimal_places=3, null=True, blank=True)
    warranty_period = models.DurationField(
        null=True,
        blank=True,
        help_text="Duration of the product warranty, e.g. 365 days.",
    )
    is_active = models.BooleanField(default=True)
    release_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to="widgets/images/", null=True, blank=True)
    datasheet = models.FileField(upload_to="widgets/datasheets/", null=True, blank=True)
    specifications = models.JSONField(
        default=dict,
        blank=True,
        help_text="Arbitrary key-value specification data.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(BaseModelMeta):
        ordering = ("name", "id")


class WidgetVariant(VuedaModel):
    """A size/material variant of a widget."""

    widget = models.ForeignKey(Widget, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=255)
    sku_suffix = models.CharField(max_length=32)
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0)

    class Meta(BaseModelMeta):
        ordering = ("widget", "name", "id")
        constraints = (
            models.UniqueConstraint(
                fields=("widget", "sku_suffix"),
                name="unique_variant_sku_per_widget",
            ),
        )


class Warehouse(VuedaModel):
    """A physical storage and distribution facility."""

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32, unique=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    address = models.TextField()
    contact_email = models.EmailField(blank=True)
    opens_at = models.TimeField()
    closes_at = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta(BaseModelMeta):
        ordering = ("name", "id")


class InventoryRecord(VuedaModel):
    """Stock levels for a widget variant at a specific warehouse."""

    formatted_name = None

    def get_formatted_name(self):
        return f"{self.variant} @ {self.warehouse.code}"

    variant = models.ForeignKey(WidgetVariant, on_delete=models.CASCADE, related_name="inventory")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="inventory")
    quantity_on_hand = models.PositiveIntegerField(default=0)
    reorder_threshold = models.PositiveSmallIntegerField(
        default=0,
        help_text="Reorder stock when quantity on hand falls below this level.",
    )
    max_stock_level = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum stock level to hold at this location.",
    )
    last_stocktake_at = models.DateTimeField(null=True, blank=True)
    last_received_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta(BaseModelMeta):
        ordering = ("warehouse", "variant")
        constraints = (
            models.UniqueConstraint(
                fields=("variant", "warehouse"),
                name="unique_inventory_per_variant_warehouse",
            ),
        )


class Promotion(VuedaModel):
    """A time-limited discount applied to a selection of widgets."""

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    valid_dates = pg_fields.DateRangeField()
    is_active = models.BooleanField(default=True)
    widgets = models.ManyToManyField(Widget, blank=True, related_name="promotions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(BaseModelMeta):
        ordering = ("-created_at", "id")


class PurchaseOrderQuerySet(models.QuerySet):
    """Queryset for purchase orders, carrying the order value annotation."""

    def with_total_value(self):
        """
        Annotate each order with the value of its lines.

        A correlated subquery rather than ``annotate(Sum("lines__..."))``. The join form
        would fan the order out to one row per line, and anything else joining a
        multi-valued relation onto the same queryset (row-level permission filtering and
        the workflow state overlay both can) would then multiply the sum. A subquery
        aggregates in its own scope, so the number is the same whatever else the viewset
        has joined.

        ``Coalesce`` to zero rather than leaving the null through: an order with no lines
        is worth nothing, and ``Sum`` over the column for the list footer would otherwise
        have to treat one null row as different from an empty page.
        """
        line_value = (
            PurchaseOrderLine.objects.filter(purchase_order=models.OuterRef("pk"))
            .order_by()
            .values("purchase_order")
            .annotate(
                value=models.Sum(
                    models.F("quantity_ordered") * models.F("unit_price"),
                    output_field=total_value_output_field(),
                )
            )
            .values("value")
        )
        return self.annotate(
            total_value=Coalesce(
                models.Subquery(line_value, output_field=total_value_output_field()),
                Decimal("0.00"),
                output_field=total_value_output_field(),
            )
        )


class PurchaseOrder(HasWorkflowModelMixin, VuedaModel):
    """
    An inbound order placed with a supplier for delivery into a warehouse.

    ``HasWorkflowModelMixin`` precedes ``VuedaModel`` so its ``save()`` runs last and can
    create the order's workflow state row once the base save has given the order an id.
    The mixin contributes no columns, only a generic relation, so it needs no migration
    of its own; the transition permissions below do.
    """

    formatted_name = None
    formatted_name_lookup_expression = "reference"

    reference = models.CharField(
        max_length=32,
        unique=True,
        help_text="Purchase order number, e.g. PO-1042.",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="inbound_purchase_orders",
        help_text="Warehouse the ordered stock is delivered to.",
    )
    order_date = models.DateField(help_text="Date the order was placed with the supplier.")
    expected_arrival_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date the supplier expects to deliver the order.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Built on FormattedNameManager rather than PurchaseOrderQuerySet.as_manager(). A
    # model whose formatted_name comes from a lookup expression, as this one's does from
    # ``reference``, depends on its default manager annotating that expression onto every
    # queryset; a plain manager shadows it and formatted_name stops resolving outside the
    # viewset. vueda_info.E009 reports it at startup, which is how this was caught.
    objects = FormattedNameManager.from_queryset(PurchaseOrderQuerySet)()

    def calculate_total_value(self):
        """
        The same number ``with_total_value`` annotates, computed in Python.

        A write response serializes the instance the write returned, which no queryset
        annotated, so the serializer falls back to this. It reads through ``lines``, which
        on a create or update has just been saved in the same transaction.
        """
        return sum(
            (line.quantity_ordered * line.unit_price for line in self.lines.all()),
            Decimal("0.00"),
        )

    class Meta(BaseModelMeta):
        ordering = ("-order_date", "-reference")
        # One permission per transition, so the workflow's TransitionPermission rows and a
        # group's grants line up one to one and a role's transitions can be read straight
        # off the group. These are ordinary Django permissions on this model's content
        # type, which is also what lets a StatePermission rule override one per state.
        permissions = (
            ("submit_purchaseorder", "Can submit purchase orders for approval"),
            ("approve_purchaseorder", "Can approve submitted purchase orders"),
            ("reject_purchaseorder", "Can reject submitted purchase orders back to draft"),
            ("receive_purchaseorder", "Can receive approved purchase orders into a warehouse"),
            ("cancel_purchaseorder", "Can cancel purchase orders"),
        )


class PurchaseOrderLine(VuedaModel):
    """A single variant, quantity, and price on a purchase order."""

    formatted_name = None
    formatted_name_lookup_expression = "variant__formatted_name"

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    variant = models.ForeignKey(
        WidgetVariant,
        on_delete=models.PROTECT,
        related_name="purchase_order_lines",
    )
    quantity_ordered = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price agreed with the supplier, which may differ from the widget's list price.",
    )

    class Meta(BaseModelMeta):
        ordering = ("purchase_order", "id")


class PurchaseOrderStateCount(VuedaModel):
    """
    One row per purchase order workflow state, carrying how many orders sit in it.

    Backed by a database view rather than a table (``managed = False``, with the SQL in
    ``catalog/sql/``), which is how this project answers "how many, grouped by what"
    without a bespoke endpoint. VUEDA has no aggregate surface beyond summing a column of
    a list, so the alternative was one filtered list request per state. That does not work
    here anyway: the workflow state filter rejects a state no order is currently in, so
    four of five requests would 400 rather than return zero. A view left-joins from the
    state table instead, so a state with no orders is a row with a count of zero.

    Nothing about consuming it is special. It is an ordinary model behind an ordinary
    VUEDA serializer, viewset, and route, with its own CRUDL permissions, so a role either
    holds ``list_purchaseorderstatecount`` or does not see the numbers at all.

    The one thing it does not inherit is row visibility. ``filter_rows_for_user`` and the
    workflow state permission overlay apply to purchase orders, not to this model, so these
    counts describe every order rather than the orders the caller may list. That is true
    today because no state rule narrows ``list_purchaseorder``; ww's only state rules deny
    ``update_purchaseorder`` to the clerk outside draft. Add a rule that hides orders from a
    list and this view has to reimplement it, or be replaced by a custom action that can
    reuse the queryset filter.
    """

    # A GeneratedField is a stored column, which a view cannot have. The value comes from
    # get_formatted_name instead, the same way InventoryRecord does it.
    formatted_name = None

    def get_formatted_name(self):
        return self.name

    state = models.ForeignKey(
        "vueda_workflow.State",
        on_delete=models.DO_NOTHING,
        related_name="+",
        help_text="The workflow state this row counts.",
    )
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    position = models.PositiveSmallIntegerField(
        help_text="Order to display the states in, following the workflow rather than the alphabet.",
    )
    order_count = models.PositiveIntegerField()

    class Meta(BaseModelMeta):
        managed = False
        db_table = "catalog_purchaseorderstatecount"
        ordering = ("position", "id")
        verbose_name = "purchase order state count"
