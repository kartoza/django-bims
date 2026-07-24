# coding=utf-8
from unittest.mock import patch
from django.db.models import signals
from django_tenants.test.cases import FastTenantTestCase

from sass.models import (
    SiteVisit,
    SiteVisitEcologicalCondition,
    SassEcologicalCategory,
    SassEcologicalCondition,
)
from sass.tests.model_factories import SiteVisitF, SiteVisitTaxonF, SassTaxonF
from bims.tests.model_factories import LocationContextGroupF, LocationContextF
from bims.models.location_context import LocationContextQuerySet


class TestSiteVisitEcologicalConditionTask(FastTenantTestCase):

    def _make_site_visit(self, **kwargs):
        """Create a SiteVisit without triggering the post_save signal."""
        receivers = signals.post_save.receivers[:]
        signals.post_save.disconnect(
            sender=SiteVisit,
            dispatch_uid=None
        )
        signals.post_save.receivers = [
            r for r in signals.post_save.receivers
            if not getattr(getattr(r[1], 'func', r[1]), '__name__', '') == 'site_visit_post_save_handler'
        ]
        try:
            return SiteVisitF.create(**kwargs)
        finally:
            signals.post_save.receivers = receivers

    def test_post_save_dispatches_task_with_tenant_schema(self):
        """post_save signal passes the current connection schema to the task."""
        from django.db import connection

        site_visit = self._make_site_visit()

        with patch(
            'sass.tasks.site_visit_ecological_condition'
            '.site_visit_ecological_condition_task.delay'
        ) as mock_delay:
            site_visit.save()

        self.assertTrue(mock_delay.called, 'Task delay should have been called')
        # Every dispatch must carry the tenant schema, not 'public'
        expected_schema = connection.schema_name
        for args, kwargs in mock_delay.call_args_list:
            self.assertEqual(
                args,
                (site_visit.id, expected_schema),
                f'Task was dispatched with wrong args: {args}',
            )

    def test_task_generates_condition_in_correct_schema(self):
        """Task creates SiteVisitEcologicalCondition inside the tenant schema."""
        from sass.tasks.site_visit_ecological_condition import (
            site_visit_ecological_condition_task,
        )

        eco_category = SassEcologicalCategory.objects.create(
            category='A',
            colour='#00FF00',
        )
        SassEcologicalCondition.objects.create(
            ecoregion_level_1='Test Region',
            geomorphological_zone='Mountain stream',
            sass_score_precentile=1,
            aspt_score_precentile=1,
            ecological_category=eco_category,
        )

        group = LocationContextGroupF.create(
            name='SA Ecoregion Level 1',
            key='eco_region_level_1',
        )
        site_visit = self._make_site_visit(sass_version=5)
        LocationContextF.create(
            site=site_visit.location_site,
            group=group,
            value='Test Region',
        )
        geo_group = LocationContextGroupF.create(
            name='Geomorphological zone',
            key='geo_class_recoded',
        )
        LocationContextF.create(
            site=site_visit.location_site,
            group=geo_group,
            value='Mountain stream',
        )
        SiteVisitTaxonF.create(
            site_visit=site_visit,
            sass_taxon=SassTaxonF.create(sass_5_score=5),
        )

        self.assertFalse(
            SiteVisitEcologicalCondition.objects.filter(
                site_visit=site_visit
            ).exists()
        )

        schema = self.tenant.schema_name
        with patch(
            'sass.scripts.site_visit_ecological_condition_generator'
            '.get_geomorphological_zone_class',
            return_value='Mountain stream',
        ), patch.object(
            LocationContextQuerySet,
            'value_from_key',
            return_value='Test Region',
        ):
            site_visit_ecological_condition_task(site_visit.id, schema)

        condition = SiteVisitEcologicalCondition.objects.filter(
            site_visit=site_visit
        ).first()
        self.assertIsNotNone(condition, 'Ecological condition should be created')
        self.assertIsNotNone(
            condition.ecological_condition,
            'Ecological category should be assigned',
        )

    def test_task_with_wrong_schema_does_not_create_condition_in_tenant(self):
        """Task dispatched in public schema cannot find the tenant site visit."""
        from sass.tasks.site_visit_ecological_condition import (
            site_visit_ecological_condition_task,
        )

        site_visit = self._make_site_visit()

        # The site_visit ID exists only in the test tenant schema, not in 'public',
        # so the task should raise DoesNotExist and leave no condition in the tenant.
        with self.assertRaises(SiteVisit.DoesNotExist):
            site_visit_ecological_condition_task(site_visit.id, 'public')

        self.assertFalse(
            SiteVisitEcologicalCondition.objects.filter(
                site_visit=site_visit
            ).exists(),
            'No condition should exist in the tenant schema',
        )
