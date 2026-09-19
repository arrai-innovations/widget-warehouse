"""
Return the demo to its seeded state, discarding everything an evaluator changed.

The three ``seed_*`` commands converge: every write is ``update_or_create``, so rerunning
them restores seeded rows to their seeded values. What they cannot do is undo. A row an
evaluator created stays, an uploaded datasheet stays, and an order walked from draft to
approved stays approved through every reseed, because ``seed_catalog`` sets an order's
seeded state only when it creates the order and ``seed_workflows`` only gives a starting
state to orders that have none. A public instance therefore runs out of drafts to submit,
which is the moment the walkthrough is built around. This command is the undo half, and it
is what a scheduled reset runs.

Catalog rows are truncated rather than deleted. The catalog models are history tracked by
pghistory, whose delete trigger writes an event row per deleted row, so an ORM delete would
fill the history views with the reset itself. TRUNCATE fires no row triggers, and
RESTART IDENTITY keeps the seeded ids stable from one reset to the next, so a bookmarked
detail URL still points at the same order tomorrow.

What is deliberately kept: the workflow definition, which ``seed_workflows`` converges on
anyway; every account outside the five demo users, including the superuser; and the
pghistory context rows, which are shared with the rest of the install.
"""

import shutil
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from ...models import Widget

# Run in the order README documents: seed_workflows looks the demo groups up by name, and
# seeding the catalog last lets each order take its initial state from the saved workflow.
SEED_COMMANDS = ("seed_demo_users", "seed_workflows", "seed_catalog")

# Object state is not a catalog table, and truncating the catalog does not reach it: it
# addresses its row through a plain integer column rather than a foreign key. Left behind,
# the states of the orders just discarded would be handed to the next seeded orders, which
# reuse the same ids.
WORKFLOW_STATE_MODELS = (("vueda_workflow", "ObjectState"), ("vueda_workflow", "ObjectStateEvent"))

CONFIRMATION = (
    "This will discard every catalog row in this database, including anything created "
    "since the last reset, and every file uploaded to it. Reseeding follows.\n"
    "Type 'yes' to continue, or anything else to abort: "
)


class Command(BaseCommand):
    help = "Discard the demo's data and reseed it, returning a public instance to its walkthrough state."

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Do not prompt for confirmation. Scheduled resets use this.",
        )

    def handle(self, *args, **options):
        if options["interactive"] and input(CONFIRMATION) != "yes":
            raise CommandError("Reset cancelled. Nothing was changed.")

        # One transaction over the discard and the reseed, so a seed that fails leaves the
        # previous demo in place rather than an empty one. TRUNCATE rolls back like any
        # other statement in PostgreSQL.
        with transaction.atomic():
            self._truncate()
            for command in SEED_COMMANDS:
                self.stdout.write(f"Running {command}")
                call_command(command, stdout=self.stdout, stderr=self.stderr)

        # After the commit, because the rows that named these files are gone either way and
        # removing a file cannot be rolled back.
        self._clear_uploads()

        self.stdout.write(self.style.SUCCESS("Demo reset."))

    def _tables(self):
        """
        Every table the demo's data lives in.

        Taken from the app registry rather than a list kept by hand, so a model added to
        the catalog is reset without anyone remembering to come back here. This picks up
        the pghistory event tables and the promotion-to-widget join table as well, since
        both are concrete models in this app.
        """
        tables = {
            model._meta.db_table
            for model in apps.get_app_config("catalog").get_models(include_auto_created=True)
            if model._meta.managed
        }
        tables.update(apps.get_model(*reference)._meta.db_table for reference in WORKFLOW_STATE_MODELS)
        return sorted(tables)

    def _truncate(self):
        tables = self._tables()
        quoted = ", ".join(connection.ops.quote_name(table) for table in tables)

        # No CASCADE. Every foreign key among these tables is inside the set, and the event
        # tables' keys are declared without a database constraint, so nothing outside is
        # reachable. Should that stop being true, PostgreSQL refuses the statement and names
        # the table, which is the failure worth having.
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {quoted} RESTART IDENTITY")

        self.stdout.write(f"  Truncated {len(tables)} table(s)")

    def _clear_uploads(self):
        """
        Remove the upload directories the catalog writes into.

        Read off the fields rather than named here, and removed whole: the seeds attach no
        files, so everything in them was uploaded by an evaluator against a row that no
        longer exists. MEDIA_ROOT itself is left alone, since it is a deployment's directory
        and may hold more than this app.
        """
        media_root = Path(settings.MEDIA_ROOT).resolve()
        field_names = ("image", "datasheet")

        for field_name in field_names:
            upload_to = Widget._meta.get_field(field_name).upload_to
            directory = (media_root / upload_to).resolve()

            # An upload_to that resolved outside MEDIA_ROOT would make this a delete of an
            # arbitrary directory. It cannot today, and it is not worth trusting.
            if not directory.is_relative_to(media_root) or directory == media_root:
                raise CommandError(f"Refusing to clear {directory}, which is not inside MEDIA_ROOT.")

            if directory.is_dir():
                shutil.rmtree(directory)
                self.stdout.write(f"  Cleared {directory}")
