from django.contrib.auth import get_user_model
from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from preferences import preferences

from bims.models import SiteSetting

User = get_user_model()


class ChecklistViewTest(FastTenantTestCase):

    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'password'
        )

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('checklist-view'))
        self.assertRedirects(resp, '/accounts/login/?next=/checklist/')

    def test_accessible_when_flag_enabled(self):
        site_setting = SiteSetting.objects.get(
            id=preferences.SiteSetting.id
        )
        site_setting.enable_checklist_versioning = True
        site_setting.save()

        self.client.login(username='testuser', password='password')
        resp = self.client.get(reverse('checklist-view'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'checklist/checklist_page.html')

    def test_not_found_when_flag_disabled(self):
        site_setting = SiteSetting.objects.get(
            id=preferences.SiteSetting.id
        )
        site_setting.enable_checklist_versioning = False
        site_setting.save()

        self.client.login(username='testuser', password='password')
        resp = self.client.get(reverse('checklist-view'))
        self.assertEqual(resp.status_code, 404)
