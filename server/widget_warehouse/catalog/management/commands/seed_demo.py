"""
Seed the demo: the five demo roles, the purchase order workflow, and the catalog.

Every write is ``update_or_create``, so this converges. Running it again restores the
seeded rows to their seeded values without discarding anything an evaluator is part way
through, which is why a deploy runs it unconditionally. ``reset_demo`` is the command that
discards those changes and seeds from scratch.
"""

from django.core.management.base import BaseCommand

from widget_warehouse.catalog.seeding import seed_demo


class Command(BaseCommand):
    help = "Seed the demo roles, the purchase order workflow, and the sample catalog."

    def handle(self, *args, **options):
        seed_demo(self.stdout, self.style)
        self.stdout.write(self.style.SUCCESS("Demo seeded."))
