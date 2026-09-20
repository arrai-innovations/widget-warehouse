"""A bulk inventory action that prepares and creates draft purchase orders.

The GET preview and POST validation share the same calculation. Inventory rows are
locked in a stable order during execution; a reviewed snapshot prevents stale plans
from silently ordering twice. A batch receipt makes transport retries idempotent.
"""

import hashlib
import json
from collections import defaultdict
from datetime import date

from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from vueda.core.permissions import filter_rows_for_user

from .models import InventoryRecord, PurchaseOrder, PurchaseOrderLine, ReplenishmentBatch, SupplierPrice

REQUIRED_PERMISSIONS = (
    "catalog.replenish_inventoryrecord",
    "catalog.list_inventoryrecord",
    "catalog.read_inventoryrecord",
    "catalog.create_purchaseorder",
    "catalog.create_purchaseorderline",
    "catalog.list_purchaseorder",
    "catalog.read_purchaseorder",
    "catalog.list_supplierprice",
)


def can_replenish(user):
    return user.is_authenticated and user.has_perms(REQUIRED_PERMISSIONS)


def require_replenishment_permission(user):
    if not can_replenish(user):
        raise PermissionDenied("You may not create replenishment orders.")


class SelectionSerializer(serializers.Serializer):
    pks = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False, max_length=500)

    def validate_pks(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Select each inventory record only once.")
        return sorted(value)


class LineSerializer(serializers.Serializer):
    inventory_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=2147483647)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    snapshot = serializers.CharField()


class SubmissionSerializer(serializers.Serializer):
    batch_id = serializers.UUIDField()
    lines = LineSerializer(many=True, allow_empty=False, max_length=500)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def selected_records(user, pks, *, lock=False):
    selection = SelectionSerializer(data={"pks": pks})
    selection.is_valid(raise_exception=True)
    pks = selection.validated_data["pks"]
    records = (
        filter_rows_for_user(InventoryRecord.objects.select_related("variant__widget__supplier"), user)
        .filter(pk__in=pks)
        .order_by("pk")
    )
    if lock:
        records = records.select_for_update(of=("self",))
    records = list(records)
    if len(records) != len(pks):
        raise ValidationError({"pks": ["Some selected inventory records are no longer available."]})
    return records


def proposals(user, records):
    # Do not mistake drafts and approval requests for confirmed incoming stock.
    # The demo has all-or-nothing receipts; partial receipts would need remaining quantities.
    variants = {record.variant_id for record in records}
    warehouses = {record.warehouse_id for record in records}
    orders = PurchaseOrder.objects.filter(destination_warehouse_id__in=warehouses).exclude(
        object_states_proxy__state__code__in=("received", "cancelled")
    )
    # Coverage must not silently exclude hidden orders and suggest duplicate purchasing.
    visible = filter_rows_for_user(orders, user)
    if orders.exclude(pk__in=visible.values("pk")).exists():
        raise PermissionDenied("Replenishment requires visibility of existing orders for these warehouses.")
    coverage = defaultdict(lambda: {"incoming": 0, "pending": 0})
    for line in PurchaseOrderLine.objects.filter(purchase_order__in=visible, variant_id__in=variants).values(
        "variant_id",
        "purchase_order__destination_warehouse_id",
        "quantity_ordered",
        "purchase_order__object_states_proxy__state__code",
    ):
        state = line["purchase_order__object_states_proxy__state__code"]
        key = (line["variant_id"], line["purchase_order__destination_warehouse_id"])
        coverage[key]["incoming" if state == "approved" else "pending"] += line["quantity_ordered"]
    prices = {
        (price.supplier_id, price.variant_id): str(price.unit_cost)
        for price in filter_rows_for_user(SupplierPrice.objects.all(), user).filter(variant_id__in=variants)
    }
    rows = []
    for record in records:
        widget = record.variant.widget
        supplier = widget.supplier
        covered = coverage[(record.variant_id, record.warehouse_id)]
        target = record.max_stock_level if record.max_stock_level is not None else record.reorder_threshold
        projected = record.quantity_on_hand + covered["incoming"] + covered["pending"]
        capacity = max(0, target - projected)
        issue = None
        if record.quantity_on_hand >= record.reorder_threshold:
            issue = "Stock is no longer below its reorder threshold."
        elif not widget.is_active or not record.warehouse.is_active:
            issue = "The product or warehouse is inactive."
        elif supplier is None:
            issue = "Assign a supplier to this product first."
        elif not supplier.is_active or supplier.is_approved is not True:
            issue = "The supplier must be active and approved."
        elif target < record.reorder_threshold:
            issue = "The maximum stock level is below the reorder threshold."
        elif projected >= record.reorder_threshold:
            issue = "Existing orders already cover the reorder threshold."
        row = {
            "inventory_id": record.pk,
            "revision": record.replenishment_revision,
            "name": record.get_formatted_name(),
            "product": widget.name,
            "variant_id": record.variant_id,
            "warehouse_id": record.warehouse_id,
            "warehouse": record.warehouse.name,
            "supplier_id": widget.supplier_id,
            "supplier": supplier.name if supplier else "No supplier",
            "on_hand": record.quantity_on_hand,
            "threshold": record.reorder_threshold,
            "target": target,
            **covered,
            "quantity": capacity if issue is None else 0,
            "unit_price": prices.get((widget.supplier_id, record.variant_id)),
            "issue": issue,
        }
        row["snapshot"] = digest(row)
        rows.append(row)
    return rows


def preview(user, pks):
    return {"rows": proposals(user, selected_records(user, pks))}


def batch_result(batch):
    return {"batch_id": str(batch.pk), "orders": list(batch.orders.order_by("pk").values("id", "reference"))}


@transaction.atomic
def execute(user, data, *, dry_run=False):
    serializer = SubmissionSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    lines = sorted(data["lines"], key=lambda line: line["inventory_id"])
    request_digest = digest(lines)
    # A unique batch receipt serializes retries, including requests with different selections.
    batch, created = ReplenishmentBatch.objects.get_or_create(
        pk=data["batch_id"], defaults={"created_by": user, "request_digest": request_digest}
    )
    if not created:
        if batch.created_by_id != user.pk or batch.request_digest != request_digest:
            raise ValidationError({"non_field_errors": ["This submission identifier has already been used."]})
        return batch_result(batch)
    records = selected_records(user, [line["inventory_id"] for line in lines], lock=True)
    rows = {row["inventory_id"]: row for row in proposals(user, records)}
    grouped = defaultdict(list)
    for line in lines:
        row = rows[line["inventory_id"]]
        if line["snapshot"] != row["snapshot"]:
            raise ValidationError(
                {"non_field_errors": [f"{row['name']}: stock, orders or pricing changed. Reload the proposals."]}
            )
        if row["issue"]:
            raise ValidationError({"non_field_errors": [f"{row['name']}: {row['issue']}"]})
        if line["quantity"] > row["quantity"]:
            raise ValidationError(
                {
                    "non_field_errors": [
                        f"{row['name']}: quantity exceeds the remaining space to the target ({row['quantity']})."
                    ]
                }
            )
        grouped[(row["supplier_id"], row["warehouse_id"])].append((row, line))
    if dry_run:
        transaction.set_rollback(True)
        return {"order_count": len(grouped)}
    InventoryRecord.objects.filter(pk__in=rows).update(replenishment_revision=F("replenishment_revision") + 1)
    for index, ((supplier_id, warehouse_id), group) in enumerate(sorted(grouped.items()), start=1):
        order = PurchaseOrder.objects.create(
            reference=f"RP-{batch.pk.hex[:20]}-{index}",
            supplier_id=supplier_id,
            destination_warehouse_id=warehouse_id,
            order_date=date.today(),
            replenishment_batch=batch,
        )
        for row, line in group:
            PurchaseOrderLine.objects.create(
                purchase_order=order,
                variant_id=row["variant_id"],
                quantity_ordered=line["quantity"],
                unit_price=line["unit_price"],
            )
    return batch_result(batch)
