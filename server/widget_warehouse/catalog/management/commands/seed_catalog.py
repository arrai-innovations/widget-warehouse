from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from django.contrib.postgres.fields.ranges import Range
from django.core.management.base import BaseCommand, CommandError
from vueda.workflow.models import ObjectState, State, Workflow

from widget_warehouse.catalog.models import (
    InventoryRecord,
    Promotion,
    PurchaseOrder,
    PurchaseOrderLine,
    Supplier,
    SupplierPrice,
    Warehouse,
    Widget,
    WidgetCategory,
    WidgetVariant,
)

# Inventory hangs off variants rather than widgets, so a widget with no variant is a widget
# no stock row can point at. Giving every bulk widget one variant is what lets inventory
# cover the catalog instead of a tenth of it.
BULK_VARIANT_SUFFIX = "STD"
BULK_VARIANT_NAME = "Standard"

# The generated inventory is deterministic rather than random: quantities cycle through
# these patterns, so two seeded instances report the same restock count and a test can pin
# it. One value in each pattern sits under the threshold, which is what puts rows in the
# "below reorder" queue on a fresh instance. Without them the flagship restock tile reads
# zero against seeded data.
BULK_QUANTITIES = (180, 96, 22, 240, 132, 64, 205, 88)
BULK_OVERFLOW_QUANTITIES = (110, 35, 74, 160)
BULK_REORDER_THRESHOLD = 50
BULK_MAX_STOCK = 400

# Every third bulk variant is also stocked in the overflow warehouse, so the warehouse
# filter has two sides to it and restocking is not a single-warehouse concern.
BULK_OVERFLOW_EVERY = 3


class Command(BaseCommand):
    help = "Seed the catalog with sample widgets, suppliers, warehouses, and promotions."

    def handle(self, *args, **options):
        self._seed_categories()
        self._seed_suppliers()
        self._seed_widgets()
        self._seed_bulk_widgets()
        self._seed_variants()
        self._seed_prices()
        self._seed_warehouses()
        self._seed_inventory()
        self._seed_promotions()
        self._seed_purchase_orders()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _seed_prices(self):
        # Example purchase costs are distinct from selling prices. Reseeding preserves
        # prices an evaluator has negotiated; reset_demo recreates the initial costs.
        for variant in WidgetVariant.objects.select_related("widget").exclude(widget__supplier=None):
            SupplierPrice.objects.get_or_create(
                supplier_id=variant.widget.supplier_id,
                variant=variant,
                defaults={
                    "unit_cost": ((variant.widget.unit_price + variant.additional_price) * Decimal("0.60")).quantize(
                        Decimal("0.01")
                    )
                },
            )

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
                    "notification_emails": [
                        "ap@precisionparts.example.com",
                        "logistics@precisionparts.example.com",
                    ],
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
                    "notification_emails": ["shipping@sinomech.example.com"],
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
                    "notification_emails": [
                        "versand@eurobearings.example.de",
                        "buchhaltung@eurobearings.example.de",
                        "qs@eurobearings.example.de",
                    ],
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
                    "notification_emails": ["accounts@pacificfasteners.example.tw"],
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
                    "notification_emails": [],
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
        self.bulk_widget_skus = []
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
                self.bulk_widget_skus.append(sku)
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

        self._seed_bulk_variants()

    def _seed_bulk_variants(self):
        """
        Give every bulk widget a single variant to hang inventory off.

        The hand-written variants above cover five widgets. The bulk widgets exist to make
        the catalog large enough to page through, and until they had variants the stock
        levels described five widgets out of sixty-three, which reads as a mostly empty
        application rather than a working one.
        """
        self.stdout.write("Seeding bulk variants...")
        for index, parent_sku in enumerate(self.bulk_widget_skus):
            obj, created = WidgetVariant.objects.update_or_create(
                widget=self.widget_objs[parent_sku],
                sku_suffix=BULK_VARIANT_SUFFIX,
                defaults={
                    "name": BULK_VARIANT_NAME,
                    "additional_price": Decimal("0.00"),
                    # The same number the Sydney inventory row below carries, so the two
                    # stock figures on a variant detail page agree with each other.
                    "stock_quantity": BULK_QUANTITIES[index % len(BULK_QUANTITIES)],
                },
            )
            self.variant_objs[f"{parent_sku}-{BULK_VARIANT_SUFFIX}"] = obj
            status = "created" if created else "exists"
            self.stdout.write(f"  Variant {parent_sku}-{BULK_VARIANT_SUFFIX}: {status}")

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

        # Five of these sit under their own reorder threshold, which is what the
        # ``below_reorder`` filter is for and what the restock queue on the landing page
        # counts. The Melbourne row for SPR-100-MD is deliberately equal to its threshold
        # rather than under it: equal is not short, and having the boundary in the seeded
        # data means the demo carries the case the filter's tests pin.
        inventory_data = [
            # (variant_key, warehouse, qty_on_hand, reorder_threshold, max_stock, last_stocktake, last_received)
            ("SPR-100-SM", syd, 48, 20, 100, now, date(2026, 3, 10)),
            ("SPR-100-MD", syd, 75, 30, 150, now, date(2026, 3, 10)),
            ("SPR-100-LG", syd, 11, 15, 60, now, date(2026, 3, 10)),
            ("SPR-200-SS", syd, 6, 10, 40, now, date(2026, 2, 28)),
            ("SPR-200-CS", syd, 38, 20, 80, now, date(2026, 2, 28)),
            ("GR-024-BRS", syd, 22, 25, 60, now, date(2026, 3, 5)),
            ("GR-024-STL", syd, 64, 25, 120, now, date(2026, 3, 5)),
            ("BRG-6204-2RS", syd, 95, 40, 200, now, date(2026, 3, 15)),
            ("BRG-6204-ZZ", syd, 140, 50, 250, now, date(2026, 3, 15)),
            ("FST-HB8-ZN", syd, 480, 200, 1000, now, date(2026, 3, 1)),
            ("FST-HB8-SS", syd, 195, 100, 500, now, date(2026, 3, 1)),
            ("SPR-100-SM", mel, 20, 10, 50, now, date(2026, 1, 20)),
            ("SPR-100-MD", mel, 15, 15, 80, now, date(2026, 1, 20)),
            ("SPR-200-CS", mel, 9, 20, 60, now, date(2026, 2, 10)),
            ("BRG-6204-2RS", mel, 40, 20, 100, now, date(2026, 2, 5)),
            ("BRG-6204-ZZ", mel, 0, 30, 120, now, date(2026, 1, 8)),
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

        self._seed_bulk_inventory(syd, mel, now)

    def _seed_bulk_inventory(self, syd, mel, now):
        """
        Stock the bulk variants, generated from a fixed pattern rather than listed.

        Listing sixty-odd rows by hand would say nothing the ten above do not. What these
        are for is volume: a stock list worth paging and filtering, and a restock queue
        with a believable number in it rather than the three or four a hand-written table
        would carry.
        """
        self.stdout.write("Seeding bulk inventory records...")
        today = date.today()
        overflow_index = 0

        for index, parent_sku in enumerate(self.bulk_widget_skus):
            variant_key = f"{parent_sku}-{BULK_VARIANT_SUFFIX}"
            rows = [(syd, BULK_QUANTITIES[index % len(BULK_QUANTITIES)])]

            if index % BULK_OVERFLOW_EVERY == 0:
                rows.append((mel, BULK_OVERFLOW_QUANTITIES[overflow_index % len(BULK_OVERFLOW_QUANTITIES)]))
                overflow_index += 1

            for warehouse, quantity in rows:
                _, created = InventoryRecord.objects.update_or_create(
                    variant=self.variant_objs[variant_key],
                    warehouse=warehouse,
                    defaults={
                        "quantity_on_hand": quantity,
                        "reorder_threshold": BULK_REORDER_THRESHOLD,
                        "max_stock_level": BULK_MAX_STOCK,
                        "last_stocktake_at": now,
                        # Spread across the last few months so the column sorts into
                        # something other than one repeated date.
                        "last_received_at": today - timedelta(days=7 + (index * 3) % 90),
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
        workflow, states = self._purchase_order_workflow()

        # Dates are relative to the seed run so a long-lived deployed instance keeps
        # orders that are plausibly in flight rather than all historical.
        #
        # The state column is what makes the order list worth looking at. Left to the
        # workflow's initial state every order sits in draft, so four of the five pipeline
        # states hold nothing and the supervisor signs in to an empty approval queue. The
        # spread below is three drafts for the clerk to submit, two orders awaiting
        # approval, and two approved orders already past their expected arrival, which is
        # the overdue work the supervisor is meant to notice.
        # (reference, supplier, warehouse, ordered_days_ago, arrival_in_days, state, lines)
        purchase_orders_data = [
            (
                "PO-1041",
                "precision-parts-co",
                "SYD-DC",
                21,
                -7,
                "approved",
                [("SPR-100-SM", 120, "12.50"), ("SPR-100-MD", 80, "14.50")],
            ),
            (
                "PO-1042",
                "precision-parts-co",
                "SYD-DC",
                10,
                8,
                "submitted",
                [("SPR-200-SS", 80, "32.99"), ("GR-024-STL", 60, "18.00")],
            ),
            (
                "PO-1043",
                "eurobearings-gmbh",
                "MEL-OVF",
                3,
                18,
                "draft",
                [("BRG-6204-2RS", 200, "10.40"), ("BRG-6204-ZZ", 150, "9.70")],
            ),
            (
                "PO-1044",
                "pacific-fasteners",
                "SYD-DC",
                0,
                None,
                "draft",
                [("FST-HB8-ZN", 1000, "0.45"), ("FST-HB8-SS", 400, "0.60")],
            ),
            (
                "PO-1045",
                "sinomech-industries",
                "SYD-DC",
                45,
                -24,
                "received",
                [("FST-HB8-ZN", 2000, "0.42")],
            ),
            (
                "PO-1046",
                "apex-components",
                "MEL-OVF",
                38,
                -26,
                "received",
                [("GSK-B002-STD", 300, "2.05")],
            ),
            (
                "PO-1047",
                "eurobearings-gmbh",
                "SYD-DC",
                14,
                2,
                "approved",
                [("BRG-6204-ZZ", 400, "9.55"), ("BRG-B004-STD", 120, "7.80")],
            ),
            (
                "PO-1048",
                "sinomech-industries",
                "MEL-OVF",
                30,
                -3,
                "approved",
                [("SPR-100-LG", 150, "16.20")],
            ),
            (
                "PO-1049",
                "pacific-fasteners",
                "SYD-DC",
                5,
                21,
                "submitted",
                [("FST-HB8-SS", 600, "0.58"), ("SPR-200-CS", 90, "24.00")],
            ),
            (
                "PO-1050",
                "apex-components",
                "SYD-DC",
                2,
                30,
                "draft",
                [("GR-024-BRS", 40, "23.50")],
            ),
            (
                "PO-1051",
                "precision-parts-co",
                "MEL-OVF",
                60,
                -41,
                "received",
                [("SPR-100-SM", 200, "12.20"), ("SPR-100-MD", 160, "14.10"), ("SPR-100-LG", 60, "16.00")],
            ),
            (
                "PO-1052",
                "sinomech-industries",
                "SYD-DC",
                26,
                None,
                "cancelled",
                [("FST-HB8-ZN", 500, "0.47")],
            ),
        ]

        for entry in purchase_orders_data:
            reference, supplier_slug, warehouse_code, ordered_days_ago, arrival_in_days, state_code, lines = entry
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

            if created:
                self._seed_order_state(workflow, states, order, state_code)

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

    def _purchase_order_workflow(self):
        """
        The purchase order workflow and its states by code, or ``(None, {})`` if unseeded.

        ``seed_workflows`` runs before this command in the documented order, so the states
        are normally here. Seeding the catalog on its own still works: every order takes
        the workflow's initial state from ``HasWorkflowModelMixin.save()``, or no state at
        all when no workflow exists yet, which the backfill in ``seed_workflows`` then
        fills in. What is lost in that case is the spread, so this says so rather than
        leaving a flat pipeline to be discovered on the dashboard.
        """
        workflow = Workflow.objects.filter(content_type=PurchaseOrder.get_content_type()).first()
        if workflow is None:
            self.stdout.write(
                self.style.WARNING(
                    "  No purchase order workflow yet, so orders keep their initial state. "
                    "Run seed_workflows, then seed_catalog again on an empty database for the seeded spread."
                )
            )
            return None, {}
        return workflow, {state.code: state for state in State.objects.filter(workflow=workflow)}

    def _seed_order_state(self, workflow, states, order, state_code):
        """
        Put a newly created order into the state the demo wants it in.

        On creation only. Reseeding a working instance deliberately does not walk an order
        back: an evaluator who submitted an order finds it still submitted afterwards, and
        ``reset_demo`` is the undo half. A fresh database, or one just reset, therefore
        gets the spread above; an instance somebody has been using keeps what happened to
        it. ``HasWorkflowModelMixin.save()`` has already written the initial state row by
        the time this runs, so this updates that row rather than adding one.
        """
        if workflow is None:
            return

        state = states.get(state_code)
        if state is None:
            raise CommandError(
                f"{order.reference} is seeded into {state_code!r}, which the purchase order workflow "
                "has no state for. Check the state codes in seed_workflows."
            )

        ObjectState.objects.update_or_create(
            workflow=workflow,
            object_id=order.id,
            defaults={"state": state},
        )
        self.stdout.write(f"    State: {state_code}")
