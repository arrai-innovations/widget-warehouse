"""
Seed the purchase order workflow: its states, transitions, and the three permission
layers VUEDA evaluates over them.

The whole definition lives here as data rather than in fixtures or in the DEBUG-only
workflow management UI, so a deployed instance reproduces it by running ``seed_demo``.
Widget Warehouse therefore does not use ``makeworkflowmigrations``: that command records
changes an operator made through the management UI, which is the workflow this project
deliberately does not use.

``seed_demo`` runs this step after the demo users, whose groups it looks up by name, and
before the catalog. A purchase order cannot be saved until this workflow exists: VUEDA
gives every saved order a state row, and raises ``WorkflowNotConfiguredError`` when the
order's model has no workflow to take an initial state from.

The three layers, in the order VUEDA evaluates them:

WorkflowPermission
    A gate on the workflow as a whole. A user without every listed permission gets a 403
    from the transition endpoints, so they see no transitions at all. Widget Warehouse
    uses ``read_purchaseorder``: whoever can read an order can see its workflow.

TransitionPermission
    What makes a single transition executable. A transition with no permission rows is
    invisible and cannot be run by anyone, superusers included, which is how a
    system-only transition is expressed.

StatePermission
    A grant or deny that overrides a baseline CRUDL permission for one state and one
    group. This is the only layer that reads the row's state, which is why VUEDA defers
    the model-level check to object level for a user whose groups hold a state grant.
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from vueda.workflow.models import (
    InitialState,
    State,
    StatePermission,
    Transition,
    TransitionPermission,
    TransitionSource,
    Workflow,
    WorkflowPermission,
)

from widget_warehouse.catalog.models import PurchaseOrder
from widget_warehouse.catalog.seeding.base import SeedStep

WORKFLOW_CODE = "purchase-order"
WORKFLOW_NAME = "Purchase Order"

INITIAL_STATE = "draft"

STATES = (
    ("draft", "Draft"),
    ("submitted", "Submitted"),
    ("approved", "Approved"),
    ("received", "Received"),
    ("cancelled", "Cancelled"),
)

# code, name, source states, target state, the permission that executes it.
# "reject" returns the order to draft rather than ending it, so a rejected order is
# open to update again by the clerk who raised it. That loop is what gives the clerk's
# draft-only narrowing something to do more than once.
TRANSITIONS = (
    ("submit", "Submit for approval", ("draft",), "submitted", "submit_purchaseorder"),
    ("approve", "Approve", ("submitted",), "approved", "approve_purchaseorder"),
    ("reject", "Reject", ("submitted",), "draft", "reject_purchaseorder"),
    ("receive", "Receive into warehouse", ("approved",), "received", "receive_purchaseorder"),
    ("cancel", "Cancel", ("draft", "submitted", "approved"), "cancelled", "cancel_purchaseorder"),
)

# The gate on the workflow as a whole. Every role that can reach a purchase order screen
# has this, including the accountant, who then sees an empty transition list because no
# transition permission matches. A role that lacked it would get a 403 from the
# transition endpoints and, because the client asks for transitions while building a
# list, an empty list view rather than a visibly refused action.
WORKFLOW_PERMISSIONS = ("read_purchaseorder",)

# state, permission, group, grant or deny.
# The clerk's baseline grants update in any state. These take it back everywhere except
# draft, which is the whole of "PO draft create/update" in the role table. The submitted
# row is the one to put in the walkthrough: same order, same URL, same clerk, and the
# update action is gone the moment they submit it, including for the clerk who raised it.
STATE_PERMISSIONS = tuple(
    (state, "update_purchaseorder", "inventory-clerk", False)
    for state in ("submitted", "approved", "received", "cancelled")
)


class PurchaseOrderWorkflow(SeedStep):
    """The purchase order workflow, its transitions, and its permission rows."""

    def run(self):
        content_type = ContentType.objects.get_for_model(PurchaseOrder)
        permissions = self._permissions(content_type)
        groups = self._groups()

        workflow = self._seed_workflow(content_type)
        states = self._seed_states(workflow)
        self._seed_initial_state(workflow, states)
        self._seed_transitions(workflow, states, permissions)
        self._seed_workflow_permissions(workflow, permissions)
        self._seed_state_permissions(states, permissions, groups)

        self.stdout.write(self.style.SUCCESS(f"Workflow {WORKFLOW_CODE} seeded."))

    def _permissions(self, content_type):
        """Every permission on the purchase order, keyed by codename."""
        wanted = {*WORKFLOW_PERMISSIONS}
        wanted.update(permission for *_, permission in TRANSITIONS)
        wanted.update(permission for _, permission, _, _ in STATE_PERMISSIONS)

        permissions = {
            permission.codename: permission
            for permission in Permission.objects.filter(content_type=content_type, codename__in=wanted)
        }

        missing = sorted(wanted - permissions.keys())
        if missing:
            raise LookupError(
                f"The purchase order workflow wants permissions that do not exist: {', '.join(missing)}. "
                "Run migrate so Django creates them, then reseed."
            )
        return permissions

    def _groups(self):
        wanted = {group for _, _, group, _ in STATE_PERMISSIONS}
        groups = {group.name: group for group in Group.objects.filter(name__in=wanted)}

        missing = sorted(wanted - groups.keys())
        if missing:
            raise LookupError(
                f"The purchase order workflow wants groups that do not exist: {', '.join(missing)}. "
                "Seed the demo users first, then reseed."
            )
        return groups

    def _seed_workflow(self, content_type):
        workflow, created = Workflow.objects.update_or_create(
            code=WORKFLOW_CODE,
            defaults={
                "name": WORKFLOW_NAME,
                "content_type": content_type,
                "historical_app_label": content_type.app_label,
                "historical_model": content_type.model,
            },
        )
        self.stdout.write(f"  Workflow {WORKFLOW_CODE}: {'created' if created else 'updated'}")
        return workflow

    def _seed_states(self, workflow):
        states = {}
        for code, name in STATES:
            state, created = State.objects.update_or_create(
                workflow=workflow,
                code=code,
                defaults={"name": name},
            )
            states[code] = state
            self.stdout.write(f"  State {code}: {'created' if created else 'updated'}")
        return states

    def _seed_initial_state(self, workflow, states):
        # A one to one on the workflow, so the lookup is the workflow alone. Changing the
        # initial state on a seeded instance repoints this row rather than adding one.
        _, created = InitialState.objects.update_or_create(
            workflow=workflow,
            defaults={"state": states[INITIAL_STATE]},
        )
        self.stdout.write(f"  Initial state {INITIAL_STATE}: {'created' if created else 'updated'}")

    def _seed_transitions(self, workflow, states, permissions):
        for code, name, sources, target, permission_codename in TRANSITIONS:
            transition, created = Transition.objects.update_or_create(
                workflow=workflow,
                code=code,
                defaults={"name": name, "target": states[target]},
            )

            for source in sources:
                TransitionSource.objects.update_or_create(
                    transition=transition,
                    source=states[source],
                    defaults={"ignored": False},
                )
            # Narrowing a transition's sources in this file has to remove the rows it no
            # longer lists, or the transition stays runnable from a state it was taken
            # out of.
            TransitionSource.objects.filter(transition=transition).exclude(
                source__code__in=sources,
            ).delete()

            TransitionPermission.objects.update_or_create(
                transition=transition,
                permission=permissions[permission_codename],
            )
            TransitionPermission.objects.filter(transition=transition).exclude(
                permission=permissions[permission_codename],
            ).delete()

            self.stdout.write(
                f"  Transition {code}: {'created' if created else 'updated'}, "
                f"{', '.join(sources)} -> {target}, needs {permission_codename}"
            )

    def _seed_workflow_permissions(self, workflow, permissions):
        for codename in WORKFLOW_PERMISSIONS:
            _, created = WorkflowPermission.objects.update_or_create(
                workflow=workflow,
                permission=permissions[codename],
            )
            self.stdout.write(f"  Workflow permission {codename}: {'created' if created else 'exists'}")

        WorkflowPermission.objects.filter(workflow=workflow).exclude(
            permission__codename__in=WORKFLOW_PERMISSIONS,
        ).delete()

    def _seed_state_permissions(self, states, permissions, groups):
        for state_code, permission_codename, group_name, grant_or_deny in STATE_PERMISSIONS:
            _, created = StatePermission.objects.update_or_create(
                state=states[state_code],
                permission=permissions[permission_codename],
                group=groups[group_name],
                defaults={"grant_or_deny": grant_or_deny},
            )
            rule = "grant" if grant_or_deny else "deny"
            self.stdout.write(
                f"  State permission {state_code}/{group_name}/{permission_codename}: "
                f"{rule}, {'created' if created else 'updated'}"
            )
