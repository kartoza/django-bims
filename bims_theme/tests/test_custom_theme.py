from django.test import TestCase
from django.contrib.sites.models import Site
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims_theme.tests.model_factories import (
    CustomThemeF
)
from bims_theme.context_processor import bims_custom_theme


class TestCustomTheme(FastTenantTestCase):

    def setUp(self):
        self.client = TenantClient(self.tenant)

    def test_new_custom_theme(self):
        """Test add new custom theme"""
        theme_name = 'main_theme'
        main_accent_color = '#FFFFFF'
        CustomThemeF.create(
            name=theme_name,
            main_accent_color=main_accent_color
        )
        self.assertEqual(
            bims_custom_theme(self)['custom_theme'].name,
            theme_name
        )
        self.assertEqual(
            bims_custom_theme(self)['custom_theme'].main_accent_color,
            main_accent_color
        )

    def test_switch_custom_theme(self):
        """Test switch custom theme"""
        theme_name_1 = '1'
        theme_name_2 = '2'
        custom_theme_1 = CustomThemeF.create(
            name=theme_name_1
        )
        CustomThemeF.create(
            name=theme_name_2
        )
        self.assertEqual(
            bims_custom_theme(self)['custom_theme'].name,
            theme_name_2
        )
        custom_theme_1.is_enabled = True
        custom_theme_1.save()
        self.assertEqual(
            bims_custom_theme(self)['custom_theme'].name,
            theme_name_1
        )

    def test_site_with_custom_theme(self):
        """Test if site is updated with custom theme"""
        main_accent_color = '#12FF21'
        site = Site.objects.first()
        CustomThemeF.create(
            main_accent_color=main_accent_color,
            site=site
        )
        response = self.client.get(
            '/'
        )
        self.assertIn(main_accent_color, response.rendered_content)
