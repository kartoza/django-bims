from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from bims.tasks import test_celery
from bims.tests.model_factories import UserF, UploadSessionF


class TestCeleryStatus(TestCase):

    def test_get_status_without_login(self):
        api_url = reverse('celery-status', kwargs={
            'task_id':'123'
        })
        client = APIClient()
        res = client.get(api_url)
        self.assertEqual(
            res.status_code, status.HTTP_401_UNAUTHORIZED
        )

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_TASK_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory', )
    def test_get_status_with_login(self):
        task = test_celery.delay()
        UploadSessionF.create(
            token=task.id,
            success_notes='success_message'
        )
        api_url = reverse('celery-status', kwargs={
            'task_id': task.id
        }) + '?session=upload'
        client = APIClient()

        user = UserF.create(is_superuser=True)
        client.login(
            username=user.username,
            password='password'
        )

        res = client.get(api_url)
        self.assertEqual(
            res.status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            res.json()['success'], 'success_message'
        )
