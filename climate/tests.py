from django.test import TestCase
from django.urls import reverse


class ClimateDashboardTests(TestCase):
    def test_dashboard_page_renders(self):
        response = self.client.get(reverse('climate:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Climate dashboard')
        self.assertIn('chart_payload', response.context)

    def test_dashboard_csv_download(self):
        response = self.client.get(reverse('climate:dashboard'), {'format': 'csv'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('.csv', response['Content-Disposition'])
