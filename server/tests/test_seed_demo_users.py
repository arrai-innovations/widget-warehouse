import pytest
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group, Permission

from widget_warehouse.catalog.seeding import DemoUsers
from widget_warehouse.catalog.seeding.users import (
    BASELINE_PERMISSIONS,
    DEMO_PASSWORD,
    DEMO_ROLES,
    codenames_for,
)


@pytest.fixture
def seeded(db):
    DemoUsers().run()


def granted(group_name):
    return {
        (app_label, codename)
        for app_label, codename in Group.objects.get(name=group_name).permissions.values_list(
            "content_type__app_label", "codename"
        )
    }


@pytest.mark.django_db
def test_every_role_gets_its_group_user_and_permissions(seeded):
    for role in DEMO_ROLES:
        user = get_user_model().objects.get(email=role["email"])
        assert user.is_active
        assert not user.is_superuser
        assert list(user.groups.values_list("name", flat=True)) == [role["group"]]
        assert granted(role["group"]) == codenames_for(role)


@pytest.mark.django_db
def test_demo_users_can_authenticate_with_the_published_password(seeded):
    for role in DEMO_ROLES:
        assert authenticate(username=role["email"], password=DEMO_PASSWORD) is not None


@pytest.mark.django_db
def test_roles_are_scoped_apart(seeded):
    clerk = get_user_model().objects.get(email="clerk@widgetwarehouse.com")
    associate = get_user_model().objects.get(email="associate@widgetwarehouse.com")
    accountant = get_user_model().objects.get(email="accountant@widgetwarehouse.com")

    # The inbound and outbound roles see different halves of the catalog. This is the
    # difference the walkthrough asks an evaluator to look at.
    assert clerk.has_perm("catalog.list_supplier")
    assert not clerk.has_perm("catalog.list_promotion")
    assert associate.has_perm("catalog.list_promotion")
    assert not associate.has_perm("catalog.list_supplier")
    assert accountant.has_perm("catalog.list_supplier")
    assert accountant.has_perm("catalog.list_promotion")

    # These roles can browse stock but cannot change counts or replenishment targets.
    for user in (clerk, associate, accountant):
        for model in ("widget", "promotion", "inventoryrecord"):
            for action in ("create", "update", "delete"):
                assert not user.has_perm(f"catalog.{action}_{model}")


@pytest.mark.django_db
def test_only_the_inventory_roles_write_purchase_orders(seeded):
    users = {role["group"]: get_user_model().objects.get(email=role["email"]) for role in DEMO_ROLES}

    for model in ("purchaseorder", "purchaseorderline"):
        # The clerk drafts and updates orders; narrowing that to draft-state orders is the
        # workflow's StatePermission job, not a baseline permission.
        assert users["inventory-clerk"].has_perm(f"catalog.create_{model}")
        assert users["inventory-clerk"].has_perm(f"catalog.update_{model}")
        assert not users["inventory-clerk"].has_perm(f"catalog.delete_{model}")

        # Deleting an order outright is what the supervisor has over the clerk.
        assert users["inventory-supervisor"].has_perm(f"catalog.delete_{model}")

        # The accountant reads orders without writing them; sales does neither.
        assert users["accountant"].has_perm(f"catalog.list_{model}")
        assert not users["accountant"].has_perm(f"catalog.create_{model}")
        for group in ("sales-associate", "sales-manager"):
            assert not users[group].has_perm(f"catalog.list_{model}")
            assert not users[group].has_perm(f"catalog.create_{model}")


@pytest.mark.django_db
def test_only_the_inbound_roles_write_suppliers(seeded):
    users = {role["group"]: get_user_model().objects.get(email=role["email"]) for role in DEMO_ROLES}

    # Both inbound roles maintain the vendor list through the supplier form.
    for group in ("inventory-clerk", "inventory-supervisor"):
        assert users[group].has_perm("catalog.create_supplier")
        assert users[group].has_perm("catalog.update_supplier")

    # Retiring a vendor is the supervisor's, the same way deleting an order is.
    assert not users["inventory-clerk"].has_perm("catalog.delete_supplier")
    assert users["inventory-supervisor"].has_perm("catalog.delete_supplier")

    # The accountant reads suppliers without writing them; the outbound roles do neither.
    assert users["accountant"].has_perm("catalog.read_supplier")
    assert not users["accountant"].has_perm("catalog.update_supplier")
    for group in ("sales-associate", "sales-manager"):
        assert not users[group].has_perm("catalog.read_supplier")
        assert not users[group].has_perm("catalog.update_supplier")


@pytest.mark.django_db
def test_baseline_permissions_reach_every_role(seeded):
    for role in DEMO_ROLES:
        assert set(BASELINE_PERMISSIONS) <= granted(role["group"])


@pytest.mark.django_db
def test_only_the_supervisor_updates_existing_inventory(seeded):
    for role in DEMO_ROLES:
        user = get_user_model().objects.get(email=role["email"])
        assert user.has_perm("catalog.update_inventoryrecord") == (role["group"] == "inventory-supervisor")
        assert not user.has_perm("catalog.create_inventoryrecord")
        assert not user.has_perm("catalog.delete_inventoryrecord")


@pytest.mark.django_db
def test_reseeding_is_idempotent_and_narrows_a_widened_group(seeded):
    clerk_group = Group.objects.get(name="inventory-clerk")
    clerk_group.permissions.add(Permission.objects.get(content_type__app_label="catalog", codename="delete_widget"))

    DemoUsers().run()

    assert Group.objects.filter(name__in=[role["group"] for role in DEMO_ROLES]).count() == len(DEMO_ROLES)
    assert get_user_model().objects.filter(email__in=[role["email"] for role in DEMO_ROLES]).count() == len(DEMO_ROLES)
    assert granted("inventory-clerk") == codenames_for(DEMO_ROLES[0])
