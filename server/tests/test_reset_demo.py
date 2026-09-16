"""
Behaviour tests for ``reset_demo``, the command a scheduled reset of the public demo runs.

What the three ``seed_*`` commands cannot do on their own is undo, so these check the
undoing: a row an evaluator created is gone, an order an evaluator advanced is back in
draft, and an uploaded file is gone with it. The rest check that the reset stops there.
It leaves accounts outside the demo alone, and it discards the catalog without writing a
delete into the history views the demo is meant to show off.
"""

from datetime import date

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from vueda.workflow.models import State

from widget_warehouse.catalog.models import PurchaseOrder, Supplier, Warehouse, Widget

WidgetEvent = apps.get_model("catalog", "WidgetEvent")
PurchaseOrderEvent = apps.get_model("catalog", "PurchaseOrderEvent")


# transactional_db rather than db: PostgreSQL refuses to TRUNCATE a table that the
# current transaction has already written to, and the wrapping transaction pytest-django
# rolls tests back with would put the seeding and the reset inside one. The command runs
# in its own transaction in a deployment, which is the case worth testing anyway.
@pytest.fixture
def seeded(transactional_db):
    call_command("seed_demo_users", verbosity=0)
    call_command("seed_workflows", verbosity=0)
    call_command("seed_catalog", verbosity=0)


def reset():
    call_command("reset_demo", "--noinput", verbosity=0)


def state_of(reference):
    return PurchaseOrder.objects.get(reference=reference).workflow_state.code


def test_a_row_an_evaluator_created_does_not_survive_the_reset(seeded):
    seeded_references = set(PurchaseOrder.objects.values_list("reference", flat=True))
    PurchaseOrder.objects.create(
        reference="PO-EVALUATOR",
        supplier=Supplier.objects.first(),
        destination_warehouse=Warehouse.objects.first(),
        order_date=date.today(),
    )

    reset()

    assert set(PurchaseOrder.objects.values_list("reference", flat=True)) == seeded_references


def test_an_advanced_order_comes_back_in_draft(seeded):
    # object_state reads through a database view on every access, so the row has to be held
    # in a local to be changed.
    object_state = PurchaseOrder.objects.get(reference="PO-1041").object_state
    object_state.state = State.objects.get(workflow=object_state.workflow, code="approved")
    object_state.save()
    assert state_of("PO-1041") == "approved"

    reset()

    # The claim the walkthrough rests on: a public instance still has drafts to submit
    # after the first visitor has been through it.
    assert state_of("PO-1041") == "draft"
    assert all(order.workflow_state.code == "draft" for order in PurchaseOrder.objects.all())


def test_an_edited_seed_row_comes_back_with_its_seeded_value(seeded):
    supplier = Supplier.objects.first()
    slug, name = supplier.slug, supplier.name
    supplier.name = "Renamed By An Evaluator"
    supplier.save()

    reset()

    assert Supplier.objects.get(slug=slug).name == name


def test_the_reset_leaves_no_delete_in_the_history(seeded):
    reset()

    # Truncating rather than deleting is what keeps this true: pghistory's delete trigger
    # would otherwise write one event per discarded row, and the history views a visitor
    # opens would be mostly resets.
    assert not WidgetEvent.objects.filter(pgh_label="delete").exists()
    assert not PurchaseOrderEvent.objects.filter(pgh_label="delete").exists()
    assert WidgetEvent.objects.count() == Widget.objects.count()


def test_accounts_outside_the_demo_are_left_alone(seeded):
    operator = get_user_model().objects.create_superuser(email="operator@example.com", password="not-the-demo")

    reset()

    operator.refresh_from_db()
    assert operator.is_superuser
    assert operator.check_password("not-the-demo")


def test_uploads_are_cleared_without_taking_the_rest_of_media_root(seeded, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    uploads = tmp_path / "widgets" / "images"
    uploads.mkdir(parents=True)
    (uploads / "evaluator.png").write_bytes(b"png")
    unrelated = tmp_path / "not-ours.txt"
    unrelated.write_text("left alone")

    reset()

    assert not uploads.exists()
    assert unrelated.exists()


def test_an_unconfirmed_interactive_reset_changes_nothing(seeded, monkeypatch):
    PurchaseOrder.objects.create(
        reference="PO-EVALUATOR",
        supplier=Supplier.objects.first(),
        destination_warehouse=Warehouse.objects.first(),
        order_date=date.today(),
    )
    monkeypatch.setattr("builtins.input", lambda *_: "no")

    with pytest.raises(CommandError):
        call_command("reset_demo", verbosity=0)

    assert PurchaseOrder.objects.filter(reference="PO-EVALUATOR").exists()
