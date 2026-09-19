from typing import ClassVar

from vueda.core.viewsets import VuedaViewSet
from vueda.workflow.models import StatePermission
from vueda.workflow.views import HasWorkflowViewMixin

from widget_warehouse.catalog.filtersets import (
    InventoryRecordFilterSet,
    PromotionFilterSet,
    PurchaseOrderFilterSet,
    PurchaseOrderStateCountFilterSet,
    SupplierFilterSet,
    WarehouseFilterSet,
    WidgetCategoryFilterSet,
    WidgetFilterSet,
    WidgetVariantFilterSet,
)
from widget_warehouse.catalog.models import (
    InventoryRecord,
    Promotion,
    PurchaseOrder,
    PurchaseOrderStateCount,
    Supplier,
    Warehouse,
    Widget,
    WidgetCategory,
    WidgetVariant,
)
from widget_warehouse.catalog.serializers import (
    InventoryRecordSerializer,
    PromotionSerializer,
    PurchaseOrderSerializer,
    PurchaseOrderStateCountSerializer,
    SupplierSerializer,
    WarehouseSerializer,
    WidgetCategorySerializer,
    WidgetSerializer,
    WidgetVariantSerializer,
)


class WidgetCategoryViewSet(VuedaViewSet):
    queryset = WidgetCategory.objects.all()
    serializer_class = WidgetCategorySerializer
    filterset_class = WidgetCategoryFilterSet


class SupplierViewSet(VuedaViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_class = SupplierFilterSet


class WidgetViewSet(VuedaViewSet):
    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer
    filterset_class = WidgetFilterSet
    permit_list_expands: ClassVar[list[str]] = ["category", "supplier"]
    ordering_fields: ClassVar[list[str]] = [
        "name",
        "slug",
        "sku",
        "category",
        "supplier",
        "unit_price",
        "weight_kg",
        "warranty_period",
        "is_active",
        "release_date",
        "created_at",
        "updated_at",
    ]
    search_fields: ClassVar[list[str]] = [
        "name",
        "slug",
        "sku",
        "description",
        "category__code",
        "category__name",
        "supplier__name",
        "supplier__slug",
    ]


class WidgetVariantViewSet(VuedaViewSet):
    queryset = WidgetVariant.objects.all()
    serializer_class = WidgetVariantSerializer
    filterset_class = WidgetVariantFilterSet
    permit_list_expands: ClassVar[list[str]] = ["widget"]


class WarehouseViewSet(VuedaViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    filterset_class = WarehouseFilterSet


class InventoryRecordViewSet(VuedaViewSet):
    """
    ``column_totals`` is VUEDA's server-side aggregate hook: the listed columns are summed
    over the filtered queryset and returned alongside the page, so the list footer totals
    every matching row rather than the ten on screen. Filter the list down to one warehouse
    and the total follows the filter.
    """

    queryset = InventoryRecord.objects.all()
    serializer_class = InventoryRecordSerializer
    filterset_class = InventoryRecordFilterSet
    permit_list_expands: ClassVar[list[str]] = ["variant", "warehouse"]
    column_totals: ClassVar[list[str]] = ["quantity_on_hand"]


class PromotionViewSet(VuedaViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    filterset_class = PromotionFilterSet


class PurchaseOrderViewSet(HasWorkflowViewMixin, VuedaViewSet):
    """
    ``HasWorkflowViewMixin`` defers the model-level permission check to object level when
    the workflow carries state permissions, because a state rule can only be decided
    against a row.
    """

    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filterset_class = PurchaseOrderFilterSet
    # "lines" is here so a list request can expand the inline as well: without it,
    # flex-fields refuses the expand on list and the create/update forms are the only
    # place the child rows are reachable.
    permit_list_expands: ClassVar[list[str]] = ["supplier", "destination_warehouse", "lines"]
    ordering_fields: ClassVar[list[str]] = [
        "reference",
        "supplier",
        "destination_warehouse",
        "order_date",
        "expected_arrival_date",
        "created_at",
        "updated_at",
    ]
    search_fields: ClassVar[list[str]] = [
        "reference",
        "supplier__name",
        "supplier__slug",
        "destination_warehouse__code",
        "destination_warehouse__name",
    ]

    def check_permissions(self, request):
        """
        Narrow the mixin's deferral to the requests it exists for.

        The mixin defers as soon as the workflow has any StatePermission row, without
        asking whether one could apply to this user, so a role with no purchase order
        permission at all reaches list and create unchallenged. Deferral is only ever
        needed for a grant rule, where the baseline says no and a state says yes; a deny
        rule narrows a permission the user already holds, so the model-level check passes
        on its own and the deny lands at object level. This defers only when the user's
        groups hold a grant rule on this workflow, and otherwise takes the ordinary path.
        """
        holds_a_state_grant = StatePermission.objects.filter(
            state__workflow__content_type=PurchaseOrder.get_content_type(),
            group__in=request.user.groups.all(),
            grant_or_deny=True,
        ).exists()
        if holds_a_state_grant:
            return super().check_permissions(request)
        return super(HasWorkflowViewMixin, self).check_permissions(request)


class PurchaseOrderStateCountViewSet(VuedaViewSet):
    """
    The order pipeline as data: one row per workflow state with its order count, in one
    request. The model is a database view, so this is an ordinary list endpoint with
    ordinary CRUDL permissions rather than a bespoke summary action.

    It reports the whole pipeline, not the caller's slice of it. See the model docstring
    for why, and for what would have to change if a state rule ever hid orders from a list.
    """

    queryset = PurchaseOrderStateCount.objects.all()
    serializer_class = PurchaseOrderStateCountSerializer
    filterset_class = PurchaseOrderStateCountFilterSet
    column_totals: ClassVar[list[str]] = ["order_count"]
