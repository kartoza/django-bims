from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.core import mail

from bims.tests.model_factories import UserF


class WetlandFeedbackViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserF.create(is_superuser=True, email='test@example.com')
        self.url = reverse('wetland-feedback')

    def test_post_with_all_data(self):
        self.client.login(username=self.user.username, password='password')

        response = self.client.post(self.url, {
            'issue': 'Test Issue',
            'description': 'Test Description',
            'issue_type': 'Type1',
            'location': '40.7128,-74.0060',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'OK'})
        self.assertEqual(len(mail.outbox), 1)  # Check that one email was sent.

    def test_missing_location(self):
        self.client.login(username=self.user.username, password='password')

        response = self.client.post(self.url, {
            'issue': 'Test Issue',
            'description': 'Test Description',
            'issue_type': 'Type1',
        })

        self.assertEqual(response.status_code, 404)  # Expecting a 404 due to missing location.

    def test_email_content(self):
        self.client.login(username=self.user.username, password='password')

        self.client.post(self.url, {
            'issue': 'Test Issue',
            'description': 'Test Description',
            'issue_type': 'Type1',
            'location': '40.7128,-74.0060',
        })

        email = mail.outbox[0]
        self.assertIn('Test Issue', email.body)
        self.assertIn('40.7128', email.body)
        self.assertIn('test@example.com', email.body)
