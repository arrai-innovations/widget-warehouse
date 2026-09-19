"""
Contract tests for the supplier's list-valued field.

``notification_emails`` is the demo's one many field, and the client renders it with
FieldSetMany because ``setupModelConfig`` names that component for it. The override is a
client-side choice, but it only resolves to a row per address if the server keeps
reporting the field as a many EmailField, so the metadata shape is asserted here
alongside the write path it feeds.
"""

from urllib.parse import urlencode

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from widget_warehouse.catalog.models import Supplier

EXPAND_PARAM = settings.REST_FLEX_FIELDS["EXPAND_PARAM"]
FIELDS_PARAM = settings.REST_FLEX_FIELDS["FIELDS_PARAM"]
MODEL_INFO_QUERY = urlencode([(FIELDS_PARAM, "model_fields"), (EXPAND_PARAM, "model_fields")])


@pytest.fixture
def supplier(db):
    return Supplier.objects.create(
        name="Precision Parts Co.",
        slug="precision-parts-co",
        contact_email="sales@example.com",
        notification_emails=["ap@example.com"],
    )


@pytest.fixture
def seeded_roles(db):
    call_command("seed_demo_users", verbosity=0)


def client_for(email):
    client = APIClient()
    client.force_authenticate(get_user_model().objects.get(email=email))
    return client


@pytest.mark.django_db
def test_model_info_reports_a_many_email_field(supplier, seeded_roles):
    info_url = reverse("info.model_info-detail", kwargs={"app_label": "catalog", "model": "supplier"})

    response = client_for("clerk@widgetwarehouse.com").get(f"{info_url}?{MODEL_INFO_QUERY}")

    assert response.status_code == 200, response.data
    field = response.data["model_fields"]["notification_emails"]
    # VUEDA picks the many mapping by these three keys. An ArrayField reports its base
    # field's type, which is what lands the lookup on the EmailField entry that carries
    # the manyComponent FieldSetMany builds each row from. Swap the model field for a
    # JSONField and type_model becomes JSONField, the lookup misses, and the row
    # component goes undefined.
    assert field["many"] is True
    assert field["type_serializer"] == "EmailField"
    assert field["type_model"] == "EmailField"
    assert field["read_only"] is False


@pytest.mark.django_db
def test_an_inbound_role_replaces_the_whole_list(supplier, seeded_roles):
    response = client_for("clerk@widgetwarehouse.com").patch(
        reverse("catalog.supplier-detail", kwargs={"pk": supplier.pk}),
        {"notification_emails": ["ap@example.com", "logistics@example.com"]},
        format="json",
    )

    assert response.status_code == 200, response.data
    supplier.refresh_from_db()
    assert supplier.notification_emails == ["ap@example.com", "logistics@example.com"]


@pytest.mark.django_db
def test_an_empty_list_is_accepted(supplier, seeded_roles):
    response = client_for("clerk@widgetwarehouse.com").patch(
        reverse("catalog.supplier-detail", kwargs={"pk": supplier.pk}),
        {"notification_emails": []},
        format="json",
    )

    assert response.status_code == 200, response.data
    supplier.refresh_from_db()
    assert supplier.notification_emails == []


@pytest.mark.django_db
def test_a_bad_address_is_rejected_by_its_position(supplier, seeded_roles):
    response = client_for("clerk@widgetwarehouse.com").patch(
        reverse("catalog.supplier-detail", kwargs={"pk": supplier.pk}),
        {"notification_emails": ["ap@example.com", "not-an-email"]},
        format="json",
    )

    # The child field errors are keyed by index, not flattened onto the field, which is
    # what lets a row-per-entry field set point at the row that failed.
    assert response.status_code == 400
    assert list(response.data["notification_emails"]) == [1]
    supplier.refresh_from_db()
    assert supplier.notification_emails == ["ap@example.com"]
