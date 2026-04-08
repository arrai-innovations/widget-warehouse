from django.db import models
from vueda.core.models import BaseModelMeta, Lookup, VuedaModel


class WidgetCategory(Lookup):
    """Type of widget: sprocket, gear, fastener, etc."""

    description = models.TextField(blank=True)

    class Meta(BaseModelMeta):
        ordering = ["name", "id"]
        verbose_name_plural = "widget categories"


class Widget(VuedaModel):
    """A hypothetical manufactured product."""

    name = models.CharField(max_length=255)
    sku = models.CharField("SKU", max_length=64, unique=True)
    category = models.ForeignKey(
        WidgetCategory,
        on_delete=models.PROTECT,
        related_name="widgets",
    )
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    weight_kg = models.DecimalField("Weight (kg)", max_digits=8, decimal_places=3, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    release_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(BaseModelMeta):
        ordering = ["name", "id"]


class WidgetVariant(VuedaModel):
    """A size/material variant of a widget."""

    widget = models.ForeignKey(Widget, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=255)
    sku_suffix = models.CharField(max_length=32)
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0)

    class Meta(BaseModelMeta):
        ordering = ["widget", "name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["widget", "sku_suffix"],
                name="unique_variant_sku_per_widget",
            ),
        ]
