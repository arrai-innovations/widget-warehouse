"""Purchase-price defaults shared by ordinary PO writes and replenishment."""

from copy import deepcopy

from rest_framework.exceptions import ValidationError

from .models import SupplierPrice


def default_line_prices(data, instance=None):
    if not isinstance(data, dict) or not isinstance(data.get("lines"), list):
        return data
    data = deepcopy(data)
    supplier_id = data.get("supplier", instance.supplier_id if instance else None)
    existing = {line.pk: line for line in instance.lines.all()} if instance else {}
    for index, line in enumerate(data["lines"]):
        if not isinstance(line, dict) or "unit_price" in line:
            continue
        old = existing.get(line.get("id"))
        variant_id = line.get("variant", old.variant_id if old else None)
        if old and str(old.variant_id) == str(variant_id) and str(instance.supplier_id) == str(supplier_id):
            line["unit_price"] = str(old.unit_price)
            continue
        if not str(supplier_id).isdigit() or not str(variant_id).isdigit():
            continue  # Let the relation fields report invalid or missing identifiers.
        price = SupplierPrice.objects.filter(supplier_id=supplier_id, variant_id=variant_id).first()
        if price is None:
            raise ValidationError(
                {f"lines.{index}.unit_price": ["Enter a price or add a supplier price for this variant."]}
            )
        line["unit_price"] = str(price.unit_cost)
    return data
