from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from django.contrib.postgres.fields.ranges import Range
from django.core.management.base import BaseCommand

from widget_warehouse.catalog.models import (
    InventoryRecord,
    Promotion,
    PurchaseOrder,
    PurchaseOrderLine,
    Supplier,
    Warehouse,
    Widget,
    WidgetCategory,
    WidgetVariant,
)


class Command(BaseCommand):
    help = "Seed the catalog with sample widgets, suppliers, warehouses, and promotions."

    def handle(self, *args, **options):
        self._seed_categories()
        self._seed_suppliers()
        self._seed_widgets()
        self._seed_bulk_widgets()
        self._seed_variants()
        self._seed_warehouses()
        self._seed_inventory()
        self._seed_promotions()
        self._seed_purchase_orders()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _seed_categories(self):
        self.stdout.write("Seeding categories...")
        categories = {
            "sprocket": ("SPROCKET", "Toothed wheels for chain or belt drives."),
            "gear": ("GEAR", "Rotating machine parts with cut teeth for torque transfer."),
            "fastener": ("FASTENER", "Hardware for mechanically joining components."),
            "bearing": ("BEARING", "Constrains relative motion, reduces friction."),
            "gasket": ("GASKET", "Seals the junction between two surfaces."),
        }
        self.cat_objs = {}
        for name, (code, desc) in categories.items():
            obj, created = WidgetCategory.objects.update_or_create(
                code=code, defaults={"name": name.title(), "description": desc}
            )
            self.cat_objs[name] = obj
            status = "created" if created else "exists"
            self.stdout.write(f"  Category {name}: {status}")

    def _seed_suppliers(self):
        self.stdout.write("Seeding suppliers...")
        suppliers_data = [
            {
                "slug": "precision-parts-co",
                "defaults": {
                    "name": "Precision Parts Co.",
                    "website": "https://www.precisionparts.example.com",
                    "contact_email": "sales@precisionparts.example.com",
                    "country": "US",
                    "reliability_score": 4.8,
                    "typical_lead_days": 7,
                    "is_approved": True,
                    "notes": "Primary supplier for sprockets and gears. ISO 9001 certified.",
                    "is_active": True,
                },
            },
            {
                "slug": "sinomech-industries",
                "defaults": {
                    "name": "SinoMech Industries",
                    "website": "https://www.sinomech.example.com",
                    "contact_email": "export@sinomech.example.com",
                    "country": "CN",
                    "reliability_score": 3.9,
                    "typical_lead_days": 21,
                    "is_approved": True,
                    "notes": "Competitive pricing on fasteners and standard components. Lead times vary.",
                    "is_active": True,
                },
            },
            {
                "slug": "eurobearings-gmbh",
                "defaults": {
                    "name": "EuroBearings GmbH",
                    "website": "https://www.eurobearings.example.de",
                    "contact_email": "info@eurobearings.example.de",
                    "country": "DE",
                    "reliability_score": 4.9,
                    "typical_lead_days": 14,
                    "is_approved": True,
                    "notes": "Premium bearings and seals. DIN/EN certified.",
                    "is_active": True,
                },
            },
            {
                "slug": "pacific-fasteners",
                "defaults": {
                    "name": "Pacific Fasteners Ltd.",
                    "website": "https://www.pacificfasteners.example.tw",
                    "contact_email": "orders@pacificfasteners.example.tw",
                    "country": "TW",
                    "reliability_score": 4.2,
                    "typical_lead_days": 18,
                    "is_approved": True,
                    "notes": "Specialises in stainless and exotic alloy fasteners.",
                    "is_active": True,
                },
            },
            {
                "slug": "apex-components",
                "defaults": {
                    "name": "Apex Components Pty Ltd",
                    "website": "https://www.apexcomponents.example.au",
                    "contact_email": "procurement@apexcomponents.example.au",
                    "country": "AU",
                    "reliability_score": None,
                    "typical_lead_days": 5,
                    "is_approved": None,
                    "notes": "Local supplier under review. Fast domestic delivery.",
                    "is_active": True,
                },
            },
        ]
        self.supplier_objs = {}
        for entry in suppliers_data:
            obj, created = Supplier.objects.update_or_create(slug=entry["slug"], defaults=entry["defaults"])
            self.supplier_objs[entry["slug"]] = obj
            status = "created" if created else "exists"
            self.stdout.write(f"  Supplier {entry['slug']}: {status}")

    def _seed_widgets(self):
        self.stdout.write("Seeding widgets...")
        # (name, slug, sku, cat_key, supplier_slug, price, weight, warranty_days, release_date, specs)
        widgets_data = [
            (
                "Standard Sprocket",
                "standard-sprocket",
                "SPR-100",
                "sprocket",
                "precision-parts-co",
                "12.50",
                "0.340",
                365,
                date(2024, 3, 15),
                {"teeth": 12, "pitch_mm": 12.7, "material": "carbon steel"},
            ),
            (
                "Heavy Duty Sprocket",
                "heavy-duty-sprocket",
                "SPR-200",
                "sprocket",
                "precision-parts-co",
                "24.99",
                "0.780",
                730,
                date(2024, 6, 1),
                {"teeth": 16, "pitch_mm": 19.05, "material": "alloy steel", "surface_treatment": "heat treated"},
            ),
            (
                "Micro Sprocket",
                "micro-sprocket",
                "SPR-050",
                "sprocket",
                "sinomech-industries",
                "6.75",
                "0.085",
                180,
                None,
                {"teeth": 8, "pitch_mm": 6.35, "material": "stainless steel"},
            ),
            (
                "Spur Gear 24T",
                "spur-gear-24t",
                "GR-024",
                "gear",
                "precision-parts-co",
                "18.00",
                "0.420",
                365,
                date(2023, 11, 1),
                {"teeth": 24, "module": 2, "pressure_angle_deg": 20},
            ),
            (
                "Helical Gear 36T",
                "helical-gear-36t",
                "GR-036",
                "gear",
                "precision-parts-co",
                "32.50",
                "0.610",
                365,
                date(2024, 1, 20),
                {"teeth": 36, "module": 2.5, "helix_angle_deg": 15, "pressure_angle_deg": 20},
            ),
            (
                "Bevel Gear Set",
                "bevel-gear-set",
                "GR-BEV",
                "gear",
                "eurobearings-gmbh",
                "45.00",
                "1.200",
                730,
                date(2025, 2, 1),
                {"ratio": "2:1", "module": 3, "material": "case hardened steel"},
            ),
            (
                "Hex Bolt M8x30",
                "hex-bolt-m8x30",
                "FST-HB8",
                "fastener",
                "pacific-fasteners",
                "0.45",
                "0.028",
                None,
                date(2022, 5, 10),
                {"thread": "M8", "length_mm": 30, "grade": "8.8", "drive": "hex"},
            ),
            (
                "Socket Cap M6x20",
                "socket-cap-m6x20",
                "FST-SC6",
                "fastener",
                "pacific-fasteners",
                "0.62",
                "0.015",
                None,
                date(2022, 5, 10),
                {"thread": "M6", "length_mm": 20, "grade": "12.9", "drive": "allen"},
            ),
            (
                "Wing Nut M10",
                "wing-nut-m10",
                "FST-WN10",
                "fastener",
                "sinomech-industries",
                "0.38",
                "0.032",
                None,
                None,
                {"thread": "M10", "material": "zinc alloy"},
            ),
            (
                "Ball Bearing 6204",
                "ball-bearing-6204",
                "BRG-6204",
                "bearing",
                "eurobearings-gmbh",
                "8.90",
                "0.120",
                730,
                date(2023, 8, 1),
                {"bore_mm": 20, "od_mm": 47, "width_mm": 14, "dynamic_load_kn": 12.7},
            ),
            (
                "Tapered Roller Bearing",
                "tapered-roller-bearing",
                "BRG-TR30",
                "bearing",
                "eurobearings-gmbh",
                "22.00",
                "0.450",
                730,
                date(2024, 4, 15),
                {"bore_mm": 30, "od_mm": 72, "width_mm": 19, "dynamic_load_kn": 48.0},
            ),
            (
                "Flat Gasket 50mm",
                "flat-gasket-50mm",
                "GSK-F50",
                "gasket",
                "apex-components",
                "2.10",
                "0.008",
                None,
                date(2024, 9, 1),
                {"od_mm": 50, "id_mm": 30, "thickness_mm": 1.5, "material": "PTFE"},
            ),
            (
                "O-Ring Kit (Assorted)",
                "o-ring-kit-assorted",
                "GSK-ORK",
                "gasket",
                "apex-components",
                "14.50",
                "0.095",
                None,
                date(2024, 9, 1),
                {"count": 50, "material": "NBR", "sizes": "M5-M20"},
            ),
        ]

        self.widget_objs = {}
        for name, slug, sku, cat_key, supplier_slug, price, weight, warranty_days, rel_date, specs in widgets_data:
            warranty = timedelta(days=warranty_days) if warranty_days else None
            obj, created = Widget.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "slug": slug,
                    "category": self.cat_objs[cat_key],
                    "supplier": self.supplier_objs.get(supplier_slug),
                    "description": "",
                    "unit_price": Decimal(price),
                    "weight_kg": Decimal(weight),
                    "warranty_period": warranty,
                    "release_date": rel_date,
                    "specifications": specs,
                },
            )
            self.widget_objs[sku] = obj
            status = "created" if created else "exists"
            self.stdout.write(f"  Widget {sku}: {status}")

    def _seed_bulk_widgets(self):
        self.stdout.write("Seeding bulk widgets for pagination testing...")
        suppliers = list(self.supplier_objs.values())
        bulk_specs = {
            "sprocket": [
                {"teeth": t, "pitch_mm": p, "material": m}
                for t, p, m in [
                    (10, 9.525, "carbon steel"),
                    (14, 12.7, "stainless steel"),
                    (18, 15.875, "alloy steel"),
                    (20, 19.05, "carbon steel"),
                    (24, 25.4, "stainless steel"),
                    (28, 12.7, "alloy steel"),
                    (32, 19.05, "carbon steel"),
                    (36, 25.4, "stainless steel"),
                    (40, 9.525, "alloy steel"),
                    (48, 12.7, "carbon steel"),
                ]
            ],
            "gear": [
                {"teeth": t, "module": m, "pressure_angle_deg": 20}
                for t, m in [
                    (12, 1),
                    (15, 1.5),
                    (18, 2),
                    (21, 2),
                    (27, 2.5),
                    (30, 3),
                    (33, 2.5),
                    (42, 3),
                    (48, 4),
                    (60, 4),
                ]
            ],
            "fastener": [
                {"thread": th, "length_mm": ln, "grade": gr, "drive": dr}
                for th, ln, gr, dr in [
                    ("M4", 10, "8.8", "hex"),
                    ("M4", 20, "10.9", "allen"),
                    ("M5", 16, "8.8", "hex"),
                    ("M5", 25, "12.9", "allen"),
                    ("M6", 12, "8.8", "hex"),
                    ("M8", 20, "10.9", "torx"),
                    ("M10", 30, "8.8", "hex"),
                    ("M10", 50, "10.9", "allen"),
                    ("M12", 40, "8.8", "hex"),
                    ("M16", 60, "10.9", "hex"),
                ]
            ],
            "bearing": [
                {"bore_mm": b, "od_mm": o, "width_mm": w, "dynamic_load_kn": d}
                for b, o, w, d in [
                    (8, 22, 7, 3.5),
                    (10, 26, 8, 4.6),
                    (12, 28, 8, 5.1),
                    (15, 35, 11, 7.8),
                    (17, 40, 12, 9.5),
                    (20, 52, 15, 15.9),
                    (25, 52, 15, 14.0),
                    (30, 62, 16, 19.5),
                    (35, 72, 17, 25.5),
                    (40, 80, 18, 30.7),
                ]
            ],
            "gasket": [
                {"od_mm": o, "id_mm": i, "thickness_mm": t, "material": m}
                for o, i, t, m in [
                    (20, 10, 1.0, "PTFE"),
                    (25, 12, 1.5, "NBR"),
                    (30, 15, 2.0, "silicone"),
                    (40, 20, 1.0, "PTFE"),
                    (50, 25, 1.5, "NBR"),
                    (60, 35, 2.0, "silicone"),
                    (75, 50, 1.5, "PTFE"),
                    (80, 55, 2.0, "NBR"),
                    (100, 70, 2.5, "silicone"),
                    (120, 90, 3.0, "PTFE"),
                ]
            ],
        }
        cat_prefixes = {
            "sprocket": ("SPR", "Sprocket"),
            "gear": ("GR", "Gear"),
            "fastener": ("FST", "Fastener"),
            "bearing": ("BRG", "Bearing"),
            "gasket": ("GSK", "Gasket"),
        }
        base_prices = {
            "sprocket": Decimal("9.00"),
            "gear": Decimal("14.00"),
            "fastener": Decimal("0.55"),
            "bearing": Decimal("6.50"),
            "gasket": Decimal("1.80"),
        }
        base_weights = {
            "sprocket": Decimal("0.250"),
            "gear": Decimal("0.300"),
            "fastener": Decimal("0.020"),
            "bearing": Decimal("0.080"),
            "gasket": Decimal("0.010"),
        }

        idx = 0
        for cat_key, specs_list in bulk_specs.items():
            prefix, label = cat_prefixes[cat_key]
            for i, specs in enumerate(specs_list, start=1):
                idx += 1
                sku = f"{prefix}-B{i:03d}"
                slug = f"{cat_key}-bulk-{i:03d}"
                name = f"{label} B{i:03d}"
                price = base_prices[cat_key] + Decimal(i) * Decimal("0.75")
                weight = base_weights[cat_key] + Decimal(i) * Decimal("0.015")
                supplier = suppliers[idx % len(suppliers)]
                obj, created = Widget.objects.update_or_create(
                    sku=sku,
                    defaults={
                        "name": name,
                        "slug": slug,
                        "category": self.cat_objs[cat_key],
                        "supplier": supplier,
                        "description": "",
                        "unit_price": price,
                        "weight_kg": weight,
                        "warranty_period": timedelta(days=365),
                        "release_date": date(2025, 1, 1),
                        "specifications": specs,
                    },
                )
                self.widget_objs[sku] = obj
                status = "created" if created else "exists"
                self.stdout.write(f"  Widget {sku}: {status}")

    def _seed_variants(self):
        self.stdout.write("Seeding variants...")
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

        self.variant_objs = {}
        for parent_sku, suffix, name, add_price, stock in variants_data:
            parent = self.widget_objs[parent_sku]
            obj, created = WidgetVariant.objects.update_or_create(
                widget=parent,
                sku_suffix=suffix,
                defaults={
                    "name": name,
                    "additional_price": Decimal(add_price),
                    "stock_quantity": stock,
                },
            )
            self.variant_objs[f"{parent_sku}-{suffix}"] = obj
            status = "created" if created else "exists"
            self.stdout.write(f"  Variant {parent_sku}-{suffix}: {status}")

    def _seed_warehouses(self):
        self.stdout.write("Seeding warehouses...")
        warehouses_data = [
            {
                "code": "SYD-DC",
                "defaults": {
                    "name": "Sydney Distribution Centre",
                    "address": "42 Industrial Drive\nSydney NSW 2000\nAustralia",
                    "contact_email": "syd.warehouse@widgetwarehouse.example.com",
                    "opens_at": "07:00",
                    "closes_at": "18:00",
                    "is_active": True,
                },
            },
            {
                "code": "MEL-OVF",
                "defaults": {
                    "name": "Melbourne Overflow",
                    "address": "17 Logistics Way\nMelbourne VIC 3000\nAustralia",
                    "contact_email": "mel.warehouse@widgetwarehouse.example.com",
                    "opens_at": "08:00",
                    "closes_at": "17:00",
                    "is_active": True,
                },
            },
            {
                "code": "BNE-STG",
                "defaults": {
                    "name": "Brisbane Staging",
                    "address": "3 Commerce Park\nBrisbane QLD 4000\nAustralia",
                    "contact_email": "bne.warehouse@widgetwarehouse.example.com",
                    "opens_at": "09:00",
                    "closes_at": "16:00",
                    "is_active": False,
                },
            },
        ]
        self.warehouse_objs = {}
        for entry in warehouses_data:
            obj, created = Warehouse.objects.update_or_create(code=entry["code"], defaults=entry["defaults"])
            self.warehouse_objs[entry["code"]] = obj
            status = "created" if created else "exists"
            self.stdout.write(f"  Warehouse {entry['code']}: {status}")

    def _seed_inventory(self):
        self.stdout.write("Seeding inventory records...")
        syd = self.warehouse_objs["SYD-DC"]
        mel = self.warehouse_objs["MEL-OVF"]
        now = datetime.now(tz=UTC)

        inventory_data = [
            # (variant_key, warehouse, qty_on_hand, reorder_threshold, max_stock, last_stocktake, last_received)
            ("SPR-100-SM", syd, 48, 20, 100, now, date(2026, 3, 10)),
            ("SPR-100-MD", syd, 75, 30, 150, now, date(2026, 3, 10)),
            ("SPR-100-LG", syd, 28, 15, 60, now, date(2026, 3, 10)),
            ("SPR-200-SS", syd, 12, 10, 40, now, date(2026, 2, 28)),
            ("SPR-200-CS", syd, 38, 20, 80, now, date(2026, 2, 28)),
            ("BRG-6204-2RS", syd, 95, 40, 200, now, date(2026, 3, 15)),
            ("BRG-6204-ZZ", syd, 140, 50, 250, now, date(2026, 3, 15)),
            ("FST-HB8-ZN", syd, 480, 200, 1000, now, date(2026, 3, 1)),
            ("FST-HB8-SS", syd, 195, 100, 500, now, date(2026, 3, 1)),
            ("SPR-100-SM", mel, 20, 10, 50, now, date(2026, 1, 20)),
            ("SPR-100-MD", mel, 30, 15, 80, now, date(2026, 1, 20)),
            ("BRG-6204-2RS", mel, 40, 20, 100, now, date(2026, 2, 5)),
        ]

        for variant_key, warehouse, qty, reorder, max_stock, stocktake, received in inventory_data:
            variant = self.variant_objs.get(variant_key)
            if not variant:
                continue
            _, created = InventoryRecord.objects.update_or_create(
                variant=variant,
                warehouse=warehouse,
                defaults={
                    "quantity_on_hand": qty,
                    "reorder_threshold": reorder,
                    "max_stock_level": max_stock,
                    "last_stocktake_at": stocktake,
                    "last_received_at": received,
                },
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  Inventory {variant_key} @ {warehouse.code}: {status}")

    def _seed_promotions(self):
        self.stdout.write("Seeding promotions...")
        sprocket_widgets = list(Widget.objects.filter(category__code="SPROCKET"))
        bearing_widgets = list(Widget.objects.filter(category__code="BEARING"))

        promotions_data = [
            {
                "code": "SPRING26",
                "defaults": {
                    "name": "Spring Clearance 2026",
                    "description": "End-of-season discount on all sprocket lines.",
                    "discount_percent": Decimal("15.00"),
                    "valid_dates": Range(lower=date(2026, 9, 1), upper=date(2026, 9, 30)),
                    "is_active": True,
                },
                "widgets": sprocket_widgets,
            },
            {
                "code": "BULK-BRG",
                "defaults": {
                    "name": "Bulk Buyer Bearing Discount",
                    "description": "10% off bearings when ordering 50 or more units.",
                    "discount_percent": Decimal("10.00"),
                    "valid_dates": Range(lower=date(2025, 7, 1), upper=date(2025, 12, 31)),
                    "is_active": False,
                },
                "widgets": bearing_widgets,
            },
            {
                "code": "LAUNCH-GR-BEV",
                "defaults": {
                    "name": "Bevel Gear Launch Promo",
                    "description": "Introductory pricing on the new bevel gear set.",
                    "discount_percent": Decimal("20.00"),
                    "valid_dates": Range(lower=date(2025, 2, 1), upper=date(2025, 4, 30)),
                    "is_active": False,
                },
                "widgets": [self.widget_objs.get("GR-BEV")] if self.widget_objs.get("GR-BEV") else [],
            },
        ]

        for entry in promotions_data:
            promo, created = Promotion.objects.update_or_create(code=entry["code"], defaults=entry["defaults"])
            if entry["widgets"]:
                promo.widgets.set(entry["widgets"])
            status = "created" if created else "exists"
            self.stdout.write(f"  Promotion {entry['code']}: {status}")

    def _seed_purchase_orders(self):
        self.stdout.write("Seeding purchase orders...")
        today = date.today()

        # Dates are relative to the seed run so a long-lived deployed instance keeps
        # orders that are plausibly in flight rather than all historical.
        # (reference, supplier_slug, warehouse_code, ordered_days_ago, arrival_in_days, lines)
        purchase_orders_data = [
            (
                "PO-1041",
                "precision-parts-co",
                "SYD-DC",
                21,
                -7,
                [("SPR-100-SM", 120, "12.50"), ("SPR-100-MD", 80, "14.50")],
            ),
            (
                "PO-1042",
                "precision-parts-co",
                "SYD-DC",
                10,
                8,
                [("SPR-200-SS", 80, "32.99"), ("GR-024-STL", 60, "18.00")],
            ),
            (
                "PO-1043",
                "eurobearings-gmbh",
                "MEL-OVF",
                3,
                18,
                [("BRG-6204-2RS", 200, "10.40"), ("BRG-6204-ZZ", 150, "9.70")],
            ),
            (
                "PO-1044",
                "pacific-fasteners",
                "SYD-DC",
                0,
                None,
                [("FST-HB8-ZN", 1000, "0.45"), ("FST-HB8-SS", 400, "0.60")],
            ),
        ]

        for reference, supplier_slug, warehouse_code, ordered_days_ago, arrival_in_days, lines in purchase_orders_data:
            order, created = PurchaseOrder.objects.update_or_create(
                reference=reference,
                defaults={
                    "supplier": self.supplier_objs[supplier_slug],
                    "destination_warehouse": self.warehouse_objs[warehouse_code],
                    "order_date": today - timedelta(days=ordered_days_ago),
                    "expected_arrival_date": (
                        today + timedelta(days=arrival_in_days) if arrival_in_days is not None else None
                    ),
                },
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  Purchase order {reference}: {status}")

            for variant_key, quantity, unit_price in lines:
                variant = self.variant_objs.get(variant_key)
                if not variant:
                    continue
                _, line_created = PurchaseOrderLine.objects.update_or_create(
                    purchase_order=order,
                    variant=variant,
                    defaults={"quantity_ordered": quantity, "unit_price": Decimal(unit_price)},
                )
                line_status = "created" if line_created else "exists"
                self.stdout.write(f"    Line {variant_key} x{quantity}: {line_status}")
