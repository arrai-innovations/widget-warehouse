"""
Seed the five demo roles the Widget Warehouse walkthrough signs in as.

Groups, their permission grants, and one user per group are defined here as data
rather than as fixtures or through the DEBUG-only permission overview UI, so the
whole role matrix reproduces on a deployed instance by running this command.

Only baseline CRUDL permissions are granted. Workflow permissions (WorkflowPermission,
TransitionPermission, StatePermission) arrive with the purchase order workflow and are
seeded alongside it; nothing in the catalog has a workflow to attach them to yet.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

# A single shared password keeps the sign-in view's credential list short enough that an
# evaluator can switch roles repeatedly without leaving the page. These accounts exist to
# be signed into by anyone looking at the demo, so the password is not a secret.
DEMO_PASSWORD = "widget-demo"

CATALOG_MODELS = ("widget", "widgetcategory", "widgetvariant")
INVENTORY_MODELS = ("inventoryrecord",)
INBOUND_MODELS = ("supplier",)
OUTBOUND_MODELS = ("promotion",)
LOCATION_MODELS = ("warehouse",)

ALL_MODELS = CATALOG_MODELS + INVENTORY_MODELS + INBOUND_MODELS + OUTBOUND_MODELS + LOCATION_MODELS

# VUEDA serves model metadata from a ContentType viewset guarded by the standard CRUDL
# permission classes, so without this the client cannot fetch model info for any model and
# every screen fails before the domain permissions above are ever consulted. Granted to all
# demo groups; it carries no domain access of its own, and model info still reports only
# the actions each role's catalog permissions allow.
BASELINE_PERMISSIONS = (("contenttypes", "read_contenttype"),)

# name, email, and read scope per role. The scopes are the "Reads" column of the
# walkthrough's role table, narrowed to the models that exist today. Every role is
# read-only at this point: the writes in that table are all purchase order and sales
# order writes, and neither model exists yet.
DEMO_ROLES = [
    {
        "group": "inventory-clerk",
        "email": "clerk@widgetwarehouse.com",
        "name": "Ilse Clerk",
        "read": CATALOG_MODELS + INVENTORY_MODELS + INBOUND_MODELS + LOCATION_MODELS,
    },
    {
        "group": "inventory-supervisor",
        "email": "supervisor@widgetwarehouse.com",
        "name": "Sam Supervisor",
        "read": CATALOG_MODELS + INVENTORY_MODELS + INBOUND_MODELS + LOCATION_MODELS,
    },
    {
        "group": "sales-associate",
        "email": "associate@widgetwarehouse.com",
        "name": "Ana Associate",
        "read": CATALOG_MODELS + INVENTORY_MODELS + OUTBOUND_MODELS + LOCATION_MODELS,
    },
    {
        "group": "sales-manager",
        "email": "manager@widgetwarehouse.com",
        "name": "Mo Manager",
        "read": CATALOG_MODELS + INVENTORY_MODELS + OUTBOUND_MODELS + LOCATION_MODELS,
    },
    {
        "group": "accountant",
        "email": "accountant@widgetwarehouse.com",
        "name": "Ada Accountant",
        "read": ALL_MODELS,
    },
]

READ_ACTIONS = ("list", "read")


def codenames_for(role):
    """Expand a role's model scope into the (app_label, codename) pairs it grants."""
    return {("catalog", f"{action}_{model}") for model in role["read"] for action in READ_ACTIONS} | set(
        BASELINE_PERMISSIONS
    )


class Command(BaseCommand):
    help = "Seed the demo roles: five groups, their catalog permissions, and one user each."

    @transaction.atomic
    def handle(self, *args, **options):
        app_labels = {app_label for app_label, _ in BASELINE_PERMISSIONS} | {"catalog"}
        permissions = {
            (permission.content_type.app_label, permission.codename): permission
            for permission in Permission.objects.filter(content_type__app_label__in=app_labels).select_related(
                "content_type"
            )
        }

        for role in DEMO_ROLES:
            group = self._seed_group(role, permissions)
            self._seed_user(role, group)

        self.stdout.write(self.style.SUCCESS(f"Demo roles seeded. Password for every demo user: {DEMO_PASSWORD}"))

    def _seed_group(self, role, permissions):
        group, created = Group.objects.get_or_create(name=role["group"])
        codenames = codenames_for(role)

        missing = sorted(codenames - permissions.keys())
        if missing:
            names = ", ".join(f"{app_label}.{codename}" for app_label, codename in missing)
            raise LookupError(
                f"Group {role['group']} wants permissions that do not exist: {names}. "
                "Run migrate so Django creates them, then reseed."
            )

        # set() rather than add() so narrowing a role's scope in this file actually
        # narrows it on the next run of an already-seeded instance.
        group.permissions.set([permissions[key] for key in sorted(codenames)])

        status = "created" if created else "updated"
        self.stdout.write(f"  Group {role['group']}: {status}, {len(codenames)} permissions")
        return group

    def _seed_user(self, role, group):
        user_model = get_user_model()
        user, created = user_model.objects.update_or_create(
            email=role["email"],
            defaults={"name": role["name"], "is_active": True, "is_superuser": False},
        )

        # Reset the password on every run so a redeployed or long-lived instance always
        # matches the credentials printed on the sign-in view.
        user.set_password(DEMO_PASSWORD)
        user.save(update_fields=["password"])
        user.groups.set([group])

        status = "created" if created else "updated"
        self.stdout.write(f"  User {role['email']}: {status}, group {group.name}")
