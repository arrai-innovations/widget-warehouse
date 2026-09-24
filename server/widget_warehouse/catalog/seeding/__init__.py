"""
The demo's seed data, as one sequence of steps.

The steps run in a fixed order because each needs what the one before it made. The
workflow step looks up the demo groups by name, and a purchase order cannot be saved
until its workflow exists. ``seed_demo`` runs them in a single transaction, so no
database ever holds a partial seed.
"""

from django.db import transaction

from widget_warehouse.catalog.seeding.catalog import Catalog
from widget_warehouse.catalog.seeding.users import DemoUsers
from widget_warehouse.catalog.seeding.workflows import PurchaseOrderWorkflow

STEPS = (DemoUsers, PurchaseOrderWorkflow, Catalog)


@transaction.atomic
def seed_demo(stdout=None, style=None):
    """Run every step in order. Each step converges, so running this again is safe."""
    for step in STEPS:
        step(stdout, style).run()


__all__ = ["STEPS", "Catalog", "DemoUsers", "PurchaseOrderWorkflow", "seed_demo"]
