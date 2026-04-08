from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from widget_warehouse.catalog.models import Widget, WidgetCategory, WidgetVariant


class Command(BaseCommand):
    help = "Seed the catalog with sample widgets."

    def handle(self, *args, **options):
        categories = {
            "sprocket": ("SPROCKET", "Toothed wheels for chain or belt drives."),
            "gear": ("GEAR", "Rotating machine parts with cut teeth for torque transfer."),
            "fastener": ("FASTENER", "Hardware for mechanically joining components."),
            "bearing": ("BEARING", "Constrains relative motion, reduces friction."),
            "gasket": ("GASKET", "Seals the junction between two surfaces."),
        }
        cat_objs = {}
        for name, (code, desc) in categories.items():
            obj, created = WidgetCategory.objects.update_or_create(
                code=code, defaults={"name": name.title(), "description": desc}
            )
            cat_objs[name] = obj
            status = "created" if created else "exists"
            self.stdout.write(f"  Category {name}: {status}")

        widgets_data = [
            ("Standard Sprocket", "SPR-100", "sprocket", "12.50", "0.340", date(2024, 3, 15)),
            ("Heavy Duty Sprocket", "SPR-200", "sprocket", "24.99", "0.780", date(2024, 6, 1)),
            ("Micro Sprocket", "SPR-050", "sprocket", "6.75", "0.085", None),
            ("Spur Gear 24T", "GR-024", "gear", "18.00", "0.420", date(2023, 11, 1)),
            ("Helical Gear 36T", "GR-036", "gear", "32.50", "0.610", date(2024, 1, 20)),
            ("Bevel Gear Set", "GR-BEV", "gear", "45.00", "1.200", date(2025, 2, 1)),
            ("Hex Bolt M8x30", "FST-HB8", "fastener", "0.45", "0.028", date(2022, 5, 10)),
            ("Socket Cap M6x20", "FST-SC6", "fastener", "0.62", "0.015", date(2022, 5, 10)),
            ("Wing Nut M10", "FST-WN10", "fastener", "0.38", "0.032", None),
            ("Ball Bearing 6204", "BRG-6204", "bearing", "8.90", "0.120", date(2023, 8, 1)),
            ("Tapered Roller Bearing", "BRG-TR30", "bearing", "22.00", "0.450", date(2024, 4, 15)),
            ("Flat Gasket 50mm", "GSK-F50", "gasket", "2.10", "0.008", date(2024, 9, 1)),
            ("O-Ring Kit (Assorted)", "GSK-ORK", "gasket", "14.50", "0.095", date(2024, 9, 1)),
        ]

        widget_objs = {}
        for name, sku, cat_key, price, weight, rel_date in widgets_data:
            obj, created = Widget.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": cat_objs[cat_key],
                    "description": "",
                    "unit_price": Decimal(price),
                    "weight_kg": Decimal(weight),
                    "release_date": rel_date,
                },
            )
            widget_objs[sku] = obj
            status = "created" if created else "exists"
            self.stdout.write(f"  Widget {sku}: {status}")

        variants_data = [
            ("SPR-100", "SM", "Small (8T)", "0.00", 50),
            ("SPR-100", "MD", "Medium (12T)", "2.00", 80),
            ("SPR-100", "LG", "Large (16T)", "4.50", 30),
            ("SPR-200", "SS", "Stainless Steel", "8.00", 15),
            ("SPR-200", "CS", "Carbon Steel", "0.00", 40),
            ("GR-024", "BRS", "Brass", "5.00", 25),
            ("GR-024", "STL", "Steel", "0.00", 60),
            ("FST-HB8", "ZN", "Zinc Plated", "0.00", 500),
            ("FST-HB8", "SS", "Stainless", "0.15", 200),
            ("BRG-6204", "2RS", "Sealed", "1.50", 100),
            ("BRG-6204", "ZZ", "Shielded", "0.80", 150),
        ]

        for parent_sku, suffix, name, add_price, stock in variants_data:
            parent = widget_objs[parent_sku]
            _, created = WidgetVariant.objects.update_or_create(
                widget=parent,
                sku_suffix=suffix,
                defaults={
                    "name": name,
                    "additional_price": Decimal(add_price),
                    "stock_quantity": stock,
                },
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  Variant {parent_sku}-{suffix}: {status}")

        self.stdout.write(self.style.SUCCESS("Seed complete."))
