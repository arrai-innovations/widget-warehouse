from datetime import date

from django.db.models import F, Q
from django_filters import rest_framework
from vueda.core.filters import VuedaFilterSet
from vueda.workflow.filtersets import HasWorkflowFilterSetMixin

from widget_warehouse.catalog.models import (
    InventoryRecord,
    Promotion,
    PurchaseOrder,
    PurchaseOrderStateCount,
    Supplier,
    SupplierPrice,
    Warehouse,
    Widget,
    WidgetCategory,
    WidgetVariant,
)

# An order in one of these states has stopped moving, so a date in the past says nothing
# about it. Named here rather than inline so the workflow's own codes are in one place.
SETTLED_ORDER_STATES = ("received", "cancelled")


class WidgetCategoryFilterSet(VuedaFilterSet):
    class Meta:
        model = WidgetCategory
        fields = ("id", "code", "name")


class SupplierFilterSet(VuedaFilterSet):
    """
    ``under_review`` asks the question the generated ``is_approved`` filter cannot.

    Approval is a three-state boolean: true approved, false rejected, null still under
    review. A generated ``BooleanFilter`` over a nullable column offers the two decided
    values and no way to ask for the undecided one, which is the only state anybody has
    work to do about. This is the same shape as the inventory list's ``below_reorder``:
    a declared filter whose method expresses what the column cannot.
    """

    under_review = rest_framework.BooleanFilter(
        method="filter_under_review",
        label="Under review",
    )

    def filter_under_review(self, queryset, name, value):
        if value is None:
            return queryset
        return queryset.filter(is_approved__isnull=value)

    class Meta:
        model = Supplier
        fields = ("id", "name", "slug", "country", "is_approved", "is_active", "under_review")


class WidgetFilterSet(VuedaFilterSet):
    name = rest_framework.CharFilter(field_name="name", label="Name", lookup_expr="icontains")
    slug = rest_framework.CharFilter(field_name="slug", label="Slug", lookup_expr="icontains")
    sku = rest_framework.CharFilter(field_name="sku", label="SKU", lookup_expr="icontains")
    sku_exact = rest_framework.CharFilter(field_name="sku", label="SKU exact", lookup_expr="iexact")
    unit_price = rest_framework.RangeFilter(field_name="unit_price", label="Unit price")
    weight_kg = rest_framework.RangeFilter(field_name="weight_kg", label="Weight (kg)")

    class Meta:
        model = Widget
        fields = ("id", "name", "slug", "sku", "category", "supplier", "unit_price", "weight_kg", "is_active")


class WidgetVariantFilterSet(VuedaFilterSet):
    class Meta:
        model = WidgetVariant
        fields = ("id", "widget", "name")


class SupplierPriceFilterSet(VuedaFilterSet):
    class Meta:
        model = SupplierPrice
        fields = ("id", "supplier", "variant")


class WarehouseFilterSet(VuedaFilterSet):
    class Meta:
        model = Warehouse
        fields = ("id", "name", "code", "is_active")


class InventoryRecordFilterSet(VuedaFilterSet):
    """
    ``below_reorder`` compares two columns of the same row, which no generated filter can
    express: the threshold is per record, not a value a request supplies. A
    ``BooleanFilter`` with a method is the hook for that, and because it is a declared
    filter VUEDA reports it in model info like any other, so the client renders it without
    knowing it is special.
    """

    below_reorder = rest_framework.BooleanFilter(
        method="filter_below_reorder",
        label="Below reorder threshold",
    )
    quantity_on_hand = rest_framework.RangeFilter(field_name="quantity_on_hand", label="Quantity on hand")

    def filter_below_reorder(self, queryset, name, value):
        if value is None:
            return queryset
        predicate = Q(quantity_on_hand__lt=F("reorder_threshold"))
        return queryset.filter(predicate) if value else queryset.exclude(predicate)

    class Meta:
        model = InventoryRecord
        fields = ("id", "variant", "warehouse", "quantity_on_hand", "below_reorder")


class PromotionFilterSet(VuedaFilterSet):
    """
    ``active_on`` is a containment test against a range column.

    ``valid_dates`` is a ``DateRangeField``, so "which promotions run on this date" is one
    ``__contains`` lookup rather than a pair of comparisons against two date columns, and
    it respects the range's own bounds: the seeded ranges are half open, so a promotion
    ending on the 30th does not run on the 30th. Nothing else in the demo exercises a
    range field as a filter.
    """

    active_on = rest_framework.DateFilter(
        field_name="valid_dates",
        lookup_expr="contains",
        label="Running on",
    )

    class Meta:
        model = Promotion
        fields = ("id", "name", "code", "is_active", "active_on")


class PurchaseOrderFilterSet(HasWorkflowFilterSetMixin, VuedaFilterSet):
    """
    ``HasWorkflowFilterSetMixin`` contributes the ``workflow_state`` filter, which is how a
    list request narrows to orders in a given state. The mixin narrows its own choices to
    the states orders are actually in, so the filter's options describe this queryset
    rather than every state the workflow defines.
    """

    replenishment_batch = rest_framework.UUIDFilter(field_name="replenishment_batch_id", label="Replenishment batch")
    reference = rest_framework.CharFilter(field_name="reference", label="Reference", lookup_expr="icontains")
    order_date = rest_framework.DateFromToRangeFilter(field_name="order_date", label="Order date")
    expected_arrival_date = rest_framework.DateFromToRangeFilter(
        field_name="expected_arrival_date",
        label="Expected arrival",
    )
    overdue = rest_framework.BooleanFilter(method="filter_overdue", label="Overdue")
    is_open = rest_framework.BooleanFilter(method="filter_is_open", label="Open")

    def filter_overdue(self, queryset, name, value):
        """
        Orders that should have arrived and have not.

        Late is two conditions, and a date comparison alone gets it wrong: an order that
        was received last month also has an arrival date in the past, and so does a
        cancelled one. Asking the client to combine a date filter with a state filter
        would not work either, because the workflow state filter refuses a state no order
        is currently in. So the question is answered here, where both halves are in reach.
        """
        if value is None:
            return queryset
        predicate = Q(expected_arrival_date__lt=date.today()) & ~Q(
            object_states_proxy__state__code__in=SETTLED_ORDER_STATES,
        )
        return queryset.filter(predicate) if value else queryset.exclude(predicate)

    def filter_is_open(self, queryset, name, value):
        """
        Orders the warehouse is still waiting on, whatever stage they have reached.

        The opposite of settled rather than a list of open states, so a state added to the
        workflow later counts as open until somebody decides it does not. An order with no
        state row at all is open too: it has not been received, and a row that predates the
        workflow is not a finished order.

        This is what the value tile on the dashboard totals. Counting open orders says how
        many are in flight; summing their value says what the warehouse has committed.
        """
        if value is None:
            return queryset
        predicate = ~Q(object_states_proxy__state__code__in=SETTLED_ORDER_STATES)
        return queryset.filter(predicate) if value else queryset.exclude(predicate)

    class Meta:
        model = PurchaseOrder
        fields = (
            "id",
            "reference",
            "supplier",
            "destination_warehouse",
            "order_date",
            "expected_arrival_date",
            "overdue",
            "is_open",
            "replenishment_batch",
        )


class PurchaseOrderStateCountFilterSet(VuedaFilterSet):
    class Meta:
        model = PurchaseOrderStateCount
        fields = ("id", "code")
