"""Chart-ready purchasing totals over complete calendar weeks, authorized as an order list."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import TruncWeek
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from widget_warehouse.catalog.models import PurchaseOrderLine, PurchaseOrderStateCount
from widget_warehouse.catalog.viewsets import PurchaseOrderViewSet


class PurchasingTrendViewSet(PurchaseOrderViewSet):
    """A single complete report, never a summary of a page of purchase orders.

    Dates are Monday through Sunday and refer to order_date, a date without a time zone.
    The response uses the VUEDA list envelope so the ordinary cancellable list adapter
    can consume it. Each row is one supplier; observations include every requested week.
    """

    def list(self, request, *args, **kwargs):
        try:
            start = date.fromisoformat(request.query_params.get("order_date_after", ""))
            end = date.fromisoformat(request.query_params.get("order_date_before", ""))
        except ValueError as error:
            raise ValidationError({"order_date": "Supply ISO start and end dates."}) from error
        days = (end - start).days + 1
        today = datetime.now(UTC).date()
        monday = today - timedelta(days=today.weekday())
        if start.weekday() != 0 or end.weekday() != 6 or not 7 <= days <= 182 or end >= monday:
            raise ValidationError({"order_date": "Choose 1 to 26 complete Monday-to-Sunday weeks before this week."})
        if request.query_params.get("purchasing") != "true":
            raise ValidationError({"purchasing": "This report requires purchasing=true."})

        # Match the list path, including row-level and workflow-state list restrictions.
        orders = self.apply_row_level_filter(self.filter_queryset(self.get_queryset()))
        groups = (
            PurchaseOrderLine.objects.filter(purchase_order_id__in=orders.values("pk"))
            .annotate(week=TruncWeek("purchase_order__order_date"))
            .values(
                "week",
                "purchase_order__supplier_id",
                "purchase_order__supplier__slug",
                "purchase_order__supplier__name",
            )
            .annotate(value=Sum(F("quantity_ordered") * F("unit_price"), output_field=DecimalField()))
            .order_by("purchase_order__supplier__slug", "week")
        )
        weeks = [(start + timedelta(days=offset)).isoformat() for offset in range(0, days, 7)]
        suppliers = {}
        for group in groups:
            pk = str(group["purchase_order__supplier_id"])
            row = suppliers.setdefault(
                pk,
                {
                    "id": pk,
                    "code": group["purchase_order__supplier__slug"],
                    "name": group["purchase_order__supplier__name"],
                    "values": dict.fromkeys(weeks, Decimal("0.00")),
                },
            )
            row["values"][group["week"].isoformat()] = group["value"]
        results = [
            {**row, "values": [{"week": week, "value": str(value)} for week, value in row["values"].items()]}
            for row in suppliers.values()
        ]
        return Response(
            {
                "results": results,
                "totalRecords": len(results),
                "totalPages": 1,
                "perPage": len(results),
                "columnTotals": {},
            }
        )


class OrderPipelineViewSet(PurchaseOrderViewSet):
    """Current states of the orders placed in a selected period, including empty states."""

    def list(self, request, *args, **kwargs):
        orders = self.apply_row_level_filter(self.filter_queryset(self.get_queryset()))
        counts = dict(
            orders.order_by()
            .values("object_states_proxy__state_id")
            .annotate(count=Count("pk", distinct=True))
            .values_list("object_states_proxy__state_id", "count")
        )
        # Reuse the view's workflow ordering and labels, but count the authorized,
        # date-filtered orders above instead of its all-time totals.
        results = [
            {**row, "order_count": counts.get(row["id"], 0)}
            for row in PurchaseOrderStateCount.objects.order_by("position", "code").values("id", "code", "name")
        ]
        return Response(
            {
                "results": results,
                "totalRecords": len(results),
                "totalPages": 1,
                "perPage": len(results),
                "columnTotals": {"order_count": sum(row["order_count"] for row in results)},
            }
        )
