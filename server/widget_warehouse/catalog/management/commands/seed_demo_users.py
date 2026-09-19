"""
Seed the five demo roles the Widget Warehouse walkthrough signs in as.

Groups, their permission grants, and one user per group are defined here as data
rather than as fixtures or through the DEBUG-only permission overview UI, so the
whole role matrix reproduces on a deployed instance by running this command.

Baseline CRUDL permissions and the per-transition permissions are granted here, because
both are ordinary Django permissions on a group. The workflow rows that consume them
(WorkflowPermission, TransitionPermission, StatePermission) belong to the workflow
definition and are seeded by ``seed_workflows``, which has to run after this command
because it looks these groups up by name.
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
# The order and its lines are always granted together: lines are only reachable as the
# order's writable inline, so a role that can change an order changes its lines too.
PURCHASE_MODELS = ("purchaseorder", "purchaseorderline")

ALL_MODELS = CATALOG_MODELS + INVENTORY_MODELS + INBOUND_MODELS + OUTBOUND_MODELS + LOCATION_MODELS + PURCHASE_MODELS

# Permissions every group needs before any screen works at all. Neither carries domain
# access of its own, and model info still reports only the actions each role's catalog
# permissions allow.
#
# contenttypes.read_contenttype: VUEDA serves model metadata from a ContentType viewset
# guarded by the standard CRUDL permission classes, so without it the client cannot fetch
# model info for any model.
#
# vueda_workflow.read_workflow: every list view asks the workflow API for the model's
# permitted transitions, and that viewset requires workflow read for any request, including
# one about a model that has no workflow. Without it the request 403s and the list renders
# empty, whether or not the model is in a workflow.
BASELINE_PERMISSIONS = (
    ("contenttypes", "read_contenttype"),
    ("vueda_workflow", "read_workflow"),
)

# name, email, and permission scopes per role, mirroring the walkthrough's role table
# narrowed to the models that exist today. "write" grants create and update, "delete"
# grants delete, "transitions" grants one permission per named transition; the sales
# roles stay read-only until the sales order arrives.
#
# Supplier writes follow the same split as purchase order writes: the inbound roles keep
# the vendor list, and only the supervisor retires a vendor outright. The split cannot go
# any finer than the model. Supplier.is_approved is a supervisor-grade decision, but a
# permission names a model and an action, so a role that may update a supplier may set
# every one of its fields; scoping one field would mean giving Supplier its own workflow.
#
# The write scopes are baseline permissions, so a purchase order write is granted here
# regardless of what state the order is in. Narrowing the clerk to draft orders only is
# the job of the StatePermission deny rules in seed_workflows.
DEMO_ROLES = [
    {
        "group": "inventory-clerk",
        "email": "clerk@widgetwarehouse.com",
        "name": "Ilse Clerk",
        "read": CATALOG_MODELS + INVENTORY_MODELS + INBOUND_MODELS + LOCATION_MODELS + PURCHASE_MODELS,
        "write": PURCHASE_MODELS + INBOUND_MODELS,
        "delete": (),
        "transitions": ("submit",),
    },
    {
        "group": "inventory-supervisor",
        "email": "supervisor@widgetwarehouse.com",
        "name": "Sam Supervisor",
        "read": CATALOG_MODELS + INVENTORY_MODELS + INBOUND_MODELS + LOCATION_MODELS + PURCHASE_MODELS,
        "write": PURCHASE_MODELS + INBOUND_MODELS,
        # The supervisor is the role that can retire an order outright, both by deleting
        # it and, now that the workflow exists, by cancelling it. Cancel is not in the
        # role table's Transitions column because the table lists the approval path;
        # someone has to be able to end an order off that path, and it is this role.
        # Retiring a supplier is the same call, so the delete scope carries both.
        "delete": PURCHASE_MODELS + INBOUND_MODELS,
        "transitions": ("submit", "approve", "reject", "receive", "cancel"),
    },
    {
        "group": "sales-associate",
        "email": "associate@widgetwarehouse.com",
        "name": "Ana Associate",
        "read": CATALOG_MODELS + INVENTORY_MODELS + OUTBOUND_MODELS + LOCATION_MODELS,
        "write": (),
        "delete": (),
        "transitions": (),
    },
    {
        "group": "sales-manager",
        "email": "manager@widgetwarehouse.com",
        "name": "Mo Manager",
        "read": CATALOG_MODELS + INVENTORY_MODELS + OUTBOUND_MODELS + LOCATION_MODELS,
        "write": (),
        "delete": (),
        "transitions": (),
    },
    {
        "group": "accountant",
        "email": "accountant@widgetwarehouse.com",
        "name": "Ada Accountant",
        "read": ALL_MODELS,
        "write": (),
        "delete": (),
        "transitions": (),
    },
]

READ_ACTIONS = ("list", "read")
WRITE_ACTIONS = ("create", "update")

# Transition permissions are per transition, so a role's Transitions column is granted
# here one codename at a time. Holding one is not enough on its own to run the
# transition: the order also has to be in a state the transition starts from, and the
# workflow's own gate permission has to be held. See seed_workflows.
TRANSITION_PERMISSIONS = {
    "submit": "submit_purchaseorder",
    "approve": "approve_purchaseorder",
    "reject": "reject_purchaseorder",
    "receive": "receive_purchaseorder",
    "cancel": "cancel_purchaseorder",
}


def codenames_for(role):
    """Expand a role's model scopes into the (app_label, codename) pairs it grants."""
    return (
        {("catalog", f"{action}_{model}") for model in role["read"] for action in READ_ACTIONS}
        | {("catalog", f"{action}_{model}") for model in role["write"] for action in WRITE_ACTIONS}
        | {("catalog", f"delete_{model}") for model in role["delete"]}
        | {("catalog", TRANSITION_PERMISSIONS[transition]) for transition in role["transitions"]}
        | set(BASELINE_PERMISSIONS)
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
