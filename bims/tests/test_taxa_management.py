from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.contrib.sites.models import Site
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from bims.tests.model_factories import (
    TaxonomyF,
    TaxonGroupF,
    SurveyF,
    BiologicalCollectionRecordF
)

User = get_user_model()


class TaxaManagementTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.permission = Permission.objects.get(codename='change_taxonomy', content_type__app_label='bims')
        self.user.user_permissions.add(self.permission)
        self.taxonomy_1 = TaxonomyF.create(
            canonical_name='taxon1',
            validated=True
        )
        self.taxonomy_2 = TaxonomyF.create(
            canonical_name='taxon1',
            validated=False,
            owner=self.user
        )
        self.taxon_group = TaxonGroupF.create(
            site=Site.objects.get_current(),
            category='SPECIES_MODULE',
            name='test',
            taxonomies=(self.taxonomy_1, self.taxonomy_2),
            experts=(self.user,)
        )

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('taxa-management'))
        self.assertRedirects(resp, '/accounts/login/?next=/taxa-management/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='testuser', password='password')
        resp = self.client.get(reverse('taxa-management'))

        self.assertEqual(str(resp.context['user']), 'testuser')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'taxa_management.html')

    def test_context_data(self):
        self.client.login(username='testuser', password='password')
        resp = self.client.get(reverse('taxa-management'), {'selected': self.taxon_group.id})

        self.assertIn('taxa_groups', resp.context)
        self.assertIn('source_collections', resp.context)
        self.assertIn('taxon_rank', resp.context)
        self.assertIn('is_expert', resp.context)
        self.assertGreater(
            len(resp.context_data['taxa_groups']),
            0
        )

    def test_validate_permission_check(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('validate-taxon'), {'pk': self.taxonomy_1.pk})
        self.assertEqual(response.status_code, 200)

        self.user.user_permissions.remove(self.permission)
        response = self.client.get(reverse('validate-taxon'))
        self.assertEqual(response.status_code, 403)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('You don\'t have permission to validate Taxon', messages[0].message)

    def test_get_with_valid_taxon(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('validate-taxon'), {'pk': self.taxonomy_1.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'status': 'success'})

    def test_get_with_invalid_taxon(self):
        self.client.login(username='testuser', password='password')
        invalid_pk = 9999
        response = self.client.get(reverse('validate-taxon'), {'pk': invalid_pk})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content.decode(), 'Object Does Not Exist')

    def test_reject_taxon_permission_check(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('reject-taxon'), {'pk': self.taxonomy_1.pk})
        self.assertEqual(response.status_code, 200)

        self.user.user_permissions.remove(self.permission)
        response = self.client.get(reverse('reject-taxon'))
        self.assertEqual(response.status_code, 403)

    def test_reject_valid_taxon(self):
        self.client.login(username='testuser', password='password')
        SurveyF.create(
            validated=False
        )
        BiologicalCollectionRecordF.create(
            taxonomy=self.taxonomy_2,
            module_group=self.taxon_group,
            validated=False
        )
        response = self.client.get(reverse('reject-taxon'),
                                   {'pk': self.taxonomy_2.pk, 'rejection_message': 'rejection_message'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(mail.outbox), 1)
        self.assertIn('rejection_message', mail.outbox[0].body)

    def test_reject_invalid_taxon(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('reject-taxon'),
                                   {'pk': 9999, 'rejection_message': 'rejection_message'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

