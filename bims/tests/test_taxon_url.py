from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from django.contrib.auth import get_user_model

from bims.models.taxon_url import TaxonURL
from bims.models.taxonomy_update_proposal import TaxonomyUpdateProposal
from bims.tests.model_factories import TaxonomyF, TaxonGroupF, IUCNStatusF
from bims.api_views.taxon_update import create_taxon_proposal

User = get_user_model()


BASE_POST = {
    'rank': 'SPECIES',
    'author': 'Test Author',
    'taxonomic_status': 'ACCEPTED',
    'accepted_taxonomy': '',
    'tags': [],
}


def _edit_url(taxonomy_id, taxon_group_id):
    return reverse('edit_taxon', kwargs={
        'id': taxonomy_id,
        'taxon_group_id': taxon_group_id,
    })


class TaxonURLModelTest(FastTenantTestCase):
    """Unit tests for the TaxonURL model itself."""

    def setUp(self):
        self.taxonomy = TaxonomyF.create(
            scientific_name='Test Species',
            canonical_name='Test Species',
        )

    def test_create_url(self):
        url = TaxonURL.objects.create(
            taxonomy=self.taxonomy,
            uri='https://example.com/taxon/1',
            label='Example Reference',
        )
        self.assertEqual(url.taxonomy, self.taxonomy)
        self.assertEqual(url.uri, 'https://example.com/taxon/1')
        self.assertEqual(url.label, 'Example Reference')

    def test_str(self):
        url = TaxonURL.objects.create(
            taxonomy=self.taxonomy,
            uri='https://example.com',
            label='My Label',
        )
        self.assertIn('My Label', str(url))
        self.assertIn('https://example.com', str(url))

    def test_ordering_by_label(self):
        TaxonURL.objects.create(taxonomy=self.taxonomy, uri='https://b.com', label='B')
        TaxonURL.objects.create(taxonomy=self.taxonomy, uri='https://a.com', label='A')
        labels = list(TaxonURL.objects.filter(taxonomy=self.taxonomy).values_list('label', flat=True))
        self.assertEqual(labels, ['A', 'B'])

    def test_cascade_delete(self):
        TaxonURL.objects.create(taxonomy=self.taxonomy, uri='https://x.com', label='X')
        self.taxonomy.delete()
        self.assertFalse(TaxonURL.objects.filter(uri='https://x.com').exists())


class TaxonURLProposalTest(FastTenantTestCase):
    """Tests for the proposal workflow: URLs stored in proposal, applied on approval."""

    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.expert = User.objects.create_user('expert', 'expert@example.com', 'password')
        self.superuser = User.objects.create_user(
            'superuser', 'super@example.com', 'password', is_superuser=True
        )
        self.parent = TaxonomyF.create(rank='GENUS', canonical_name='TestGenus')
        self.taxonomy = TaxonomyF.create(
            scientific_name='Test Species',
            canonical_name='Test Species',
            parent=self.parent,
            rank='SPECIES',
        )
        self.taxon_group = TaxonGroupF.create(
            name='Test Group',
            taxonomies=(self.taxonomy,),
            experts=(self.expert,),
        )
        self.iucn_status = IUCNStatusF.create()

    def _post(self, user, extra=None):
        self.client.login(username=user.username, password='password')
        data = {
            **BASE_POST,
            'taxon_name': 'TestGenus Species',
            'iucn_status': self.iucn_status.id,
            'parent': self.parent.id,
        }
        if extra:
            data.update(extra)
        response = self.client.post(
            _edit_url(self.taxonomy.id, self.taxon_group.id), data
        )
        self.client.logout()
        return response

    def _pending_proposal(self):
        return TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            status='pending',
        ).first()

    # ------------------------------------------------------------------
    # Submitting URLs stores them in the proposal, not on the taxonomy
    # ------------------------------------------------------------------

    def test_submitted_urls_stored_in_proposal_additional_data(self):
        response = self._post(self.expert, {
            'url_uri': ['https://example.com/ref1'],
            'url_label': ['Reference One'],
            'url_id': [''],
        })
        self.assertEqual(response.status_code, 302)

        proposal = self._pending_proposal()
        self.assertIsNotNone(proposal)
        proposed = proposal.additional_data.get('proposed_urls', [])
        self.assertEqual(len(proposed), 1)
        self.assertEqual(proposed[0]['uri'], 'https://example.com/ref1')
        self.assertEqual(proposed[0]['label'], 'Reference One')
        self.assertIsNone(proposed[0]['id'])

    def test_urls_not_applied_to_taxonomy_before_approval(self):
        self._post(self.expert, {
            'url_uri': ['https://example.com/ref1'],
            'url_label': ['Reference One'],
            'url_id': [''],
        })
        self.assertFalse(TaxonURL.objects.filter(taxonomy=self.taxonomy).exists())

    def test_multiple_urls_stored(self):
        self._post(self.expert, {
            'url_uri': ['https://a.com', 'https://b.com'],
            'url_label': ['Alpha', 'Beta'],
            'url_id': ['', ''],
        })
        proposal = self._pending_proposal()
        proposed = proposal.additional_data['proposed_urls']
        self.assertEqual(len(proposed), 2)
        uris = {u['uri'] for u in proposed}
        self.assertIn('https://a.com', uris)
        self.assertIn('https://b.com', uris)

    def test_empty_uri_rows_are_skipped(self):
        self._post(self.expert, {
            'url_uri': ['https://valid.com', ''],
            'url_label': ['Valid', ''],
            'url_id': ['', ''],
        })
        proposal = self._pending_proposal()
        proposed = proposal.additional_data['proposed_urls']
        self.assertEqual(len(proposed), 1)
        self.assertEqual(proposed[0]['uri'], 'https://valid.com')

    def test_no_urls_submitted_stores_empty_list(self):
        self._post(self.expert)
        proposal = self._pending_proposal()
        self.assertEqual(proposal.additional_data.get('proposed_urls'), [])

    # ------------------------------------------------------------------
    # Approval applies URLs to the taxonomy
    # ------------------------------------------------------------------

    def test_approve_creates_taxon_url_objects(self):
        self._post(self.expert, {
            'url_uri': ['https://example.com/ref1'],
            'url_label': ['Reference One'],
            'url_id': [''],
        })
        proposal = self._pending_proposal()
        proposal.approve(self.superuser, suppress_emails=True)

        urls = TaxonURL.objects.filter(taxonomy=self.taxonomy)
        self.assertEqual(urls.count(), 1)
        self.assertEqual(urls.first().uri, 'https://example.com/ref1')
        self.assertEqual(urls.first().label, 'Reference One')

    def test_approve_removes_deleted_urls(self):
        existing = TaxonURL.objects.create(
            taxonomy=self.taxonomy,
            uri='https://old.com',
            label='Old Link',
        )
        # Submit proposal with the old URL omitted (user deleted it)
        self._post(self.expert, {
            'url_uri': ['https://new.com'],
            'url_label': ['New Link'],
            'url_id': [''],
        })
        proposal = self._pending_proposal()
        proposal.approve(self.superuser, suppress_emails=True)

        self.assertFalse(TaxonURL.objects.filter(id=existing.id).exists())
        self.assertTrue(TaxonURL.objects.filter(uri='https://new.com').exists())

    def test_approve_updates_existing_url(self):
        existing = TaxonURL.objects.create(
            taxonomy=self.taxonomy,
            uri='https://old.com',
            label='Old Label',
        )
        # Submit with the same ID but updated values
        self._post(self.expert, {
            'url_uri': ['https://updated.com'],
            'url_label': ['Updated Label'],
            'url_id': [str(existing.id)],
        })
        proposal = self._pending_proposal()
        proposal.approve(self.superuser, suppress_emails=True)

        existing.refresh_from_db()
        self.assertEqual(existing.uri, 'https://updated.com')
        self.assertEqual(existing.label, 'Updated Label')

    def test_approve_strips_proposed_urls_from_additional_data(self):
        self._post(self.expert, {
            'url_uri': ['https://example.com'],
            'url_label': ['Example'],
            'url_id': [''],
        })
        proposal = self._pending_proposal()
        proposal.approve(self.superuser, suppress_emails=True)

        self.taxonomy.refresh_from_db()
        self.assertNotIn('proposed_urls', self.taxonomy.additional_data or {})

    # ------------------------------------------------------------------
    # Rejection leaves the taxonomy unchanged
    # ------------------------------------------------------------------

    def test_reject_does_not_apply_urls(self):
        self._post(self.expert, {
            'url_uri': ['https://example.com/ref1'],
            'url_label': ['Reference One'],
            'url_id': [''],
        })
        proposal = self._pending_proposal()
        proposal.reject_data(reviewer=self.superuser)

        self.assertFalse(TaxonURL.objects.filter(taxonomy=self.taxonomy).exists())

    def test_reject_preserves_existing_urls(self):
        existing = TaxonURL.objects.create(
            taxonomy=self.taxonomy,
            uri='https://existing.com',
            label='Existing',
        )
        # Propose removing it
        self._post(self.expert, {
            'url_uri': [],
            'url_label': [],
            'url_id': [],
        })
        proposal = self._pending_proposal()
        proposal.reject_data(reviewer=self.superuser)

        self.assertTrue(TaxonURL.objects.filter(id=existing.id).exists())

    # ------------------------------------------------------------------
    # Re-editing with a pending proposal shows proposed URLs in the form
    # ------------------------------------------------------------------

    def test_edit_form_shows_proposed_urls_not_live_urls(self):
        TaxonURL.objects.create(
            taxonomy=self.taxonomy,
            uri='https://live.com',
            label='Live URL',
        )
        # Create a proposal that removes the live URL
        self._post(self.expert, {
            'url_uri': ['https://proposed.com'],
            'url_label': ['Proposed URL'],
            'url_id': [''],
        })
        self.client.login(username='expert', password='password')
        response = self.client.get(_edit_url(self.taxonomy.id, self.taxon_group.id))
        self.assertEqual(response.status_code, 200)
        taxon_urls = list(response.context['taxon_urls'])
        uris = [u['uri'] if isinstance(u, dict) else u.uri for u in taxon_urls]
        self.assertIn('https://proposed.com', uris)
        self.assertNotIn('https://live.com', uris)

    # ------------------------------------------------------------------
    # Proposal API serializer returns proposed URLs
    # ------------------------------------------------------------------

    def test_proposal_api_returns_proposed_urls(self):
        self._post(self.expert, {
            'url_uri': ['https://proposal-api.com'],
            'url_label': ['API Ref'],
            'url_id': [''],
        })
        proposal = self._pending_proposal()
        self.client.login(username='superuser', password='password')
        response = self.client.get(f'/api/taxon-proposal/{proposal.id}/')
        self.assertEqual(response.status_code, 200)
        urls = response.json().get('urls', [])
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]['uri'], 'https://proposal-api.com')
        self.assertEqual(urls[0]['label'], 'API Ref')

    def test_proposal_api_returns_live_urls_when_no_proposed_urls(self):
        TaxonURL.objects.create(
            taxonomy=self.taxonomy,
            uri='https://live.com',
            label='Live',
        )
        proposal = create_taxon_proposal(
            taxon=self.taxonomy,
            taxon_group=self.taxon_group,
            creator=self.expert,
        )
        self.client.login(username='superuser', password='password')
        response = self.client.get(f'/api/taxon-proposal/{proposal.id}/')
        self.assertEqual(response.status_code, 200)
        urls = response.json().get('urls', [])
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]['uri'], 'https://live.com')
