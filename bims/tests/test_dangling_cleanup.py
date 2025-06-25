# tests/test_dangling_cleanup.py
from types import SimpleNamespace
from unittest.mock import patch

from django.core import mail
from django.core.mail import EmailMessage
from django.db import connection
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase
from django.utils import timezone

from bims.models import (
    Survey,
    SurveyData,
    SurveyDataOption,
    SurveyDataValue,
)
from bims.tests.model_factories import (
    SurveyF,
    LocationContextF,
    LocationSiteF
)
from bims.models.location_site import LocationSite
from bims.models.location_context import LocationContext
from django.contrib.auth import get_user_model

from bims.tasks.location_site import _dangling_queryset, remove_dangling_sites


@override_settings(
    DEFAULT_FROM_EMAIL="noreply@example.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class DanglingCleanupTests(FastTenantTestCase):
    """Integration-style tests for `_dangling_queryset` and the
    `remove_dangling_sites` task."""

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _create_user(self):
        User = get_user_model()
        return User.objects.create_superuser(
            "admin@example.com", "admin@example.com", "password"
        )

    def _create_full_survey(self, site):
        """Survey with *child* data so it is *not* dangling."""
        survey = SurveyF.create(site=site, date=timezone.now())
        sdata = SurveyData.objects.create(name="Temp")
        opt = SurveyDataOption.objects.create(survey_data=sdata, option="Hot")
        SurveyDataValue.objects.create(
            survey=survey, survey_data=sdata, survey_data_option=opt
        )
        return survey

    # ------------------------------------------------------------------ #
    # 1. _dangling_queryset logic
    # ------------------------------------------------------------------ #
    def test_dangling_queryset_for_survey(self):
        # dangling
        dangling = SurveyF.create(date=timezone.now())

        # not dangling
        site = LocationSiteF.create(name="Foo")
        kept = self._create_full_survey(site)

        qs = _dangling_queryset(Survey)
        self.assertIn(dangling, qs)
        self.assertNotIn(kept, qs)

    def test_dangling_queryset_for_location_site_skip_logic(self):
        # site1 → dangling (no relations)
        site1 = LocationSiteF.create(name="Site-1")

        # site2 → NOT dangling (has survey)
        site2 = LocationSiteF.create(name="Site-2")
        self._create_full_survey(site2)

        # site3 → still dangling even though it has LocationContext
        site3 = LocationSiteF.create(name="Site-3")
        LocationContextF.create(site=site3)

        qs = _dangling_queryset(
            LocationSite, skip_models=frozenset({LocationContext})
        )
        self.assertQuerysetEqual(
            qs.order_by("id"),
            [site1, site3],
            transform=lambda x: x,
            ordered=True,
        )

    # ------------------------------------------------------------------ #
    # 2. remove_dangling_sites task end-to-end
    # ------------------------------------------------------------------ #
    @patch("bims.tasks.location_site.log")  # silence logging in test output
    def test_remove_dangling_sites_deletes_and_emails(self, _mock_log):
        self._create_user()  # super-user who will receive e-mail

        # ─── Test data ────────────────────────────────────────────────
        # Surveys
        site_kept = LocationSiteF.create(name="Kept")
        self._create_full_survey(site_kept)

        # LocationSite
        site_removed1 = LocationSiteF.create(name="ToRemove-1")
        site_removed2 = LocationSiteF.create(name="ToRemove-2")
        dangling_survey = SurveyF.create(date=timezone.now(), site=site_removed2)
        LocationContextF.create(site=site_removed2)

        # Assert LocationSite
        self.assertEqual(Survey.objects.count(), 2)
        self.assertEqual(LocationSite.objects.count(), 3)

        # ─── Tenant patch so the subject shows a name ────────────────
        orig_tenant = getattr(connection, "tenant", None)
        connection.tenant = SimpleNamespace(name="Acme")

        try:
            remove_dangling_sites()  # call the task synchronously
        finally:
            # restore
            if orig_tenant is not None:
                connection.tenant = orig_tenant
            else:
                delattr(connection, "tenant")

        # ─── Assertions ───────────────────────────────────────────────
        # Data removed / kept
        self.assertFalse(Survey.objects.filter(id=dangling_survey.id).exists())
        self.assertTrue(Survey.objects.filter(site=site_kept).exists())
        self.assertFalse(LocationSite.objects.filter(id=site_removed1.id).exists())
        self.assertFalse(LocationSite.objects.filter(id=site_removed2.id).exists())
        self.assertTrue(LocationSite.objects.filter(id=site_kept.id).exists())

        # Mail sent
        self.assertEqual(len(mail.outbox), 1)
        email: EmailMessage = mail.outbox[0]
        self.assertIn("[Acme] Dangling data cleanup report", email.subject)
        self.assertIn("Surveys deleted       : 1/1", email.body)
        self.assertIn("Location sites deleted: 2/2", email.body)
