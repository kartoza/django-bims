import datetime
from django.urls import reverse
from django.test import TestCase
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework import status
from django.contrib.auth import get_user_model
from bims.models.taxonomy_update_proposal import TaxonomyUpdateProposal
from bims.tests.model_factories import (
    TaxonomyF,
    TaxonGroupF,
    TaxonomyUpdateProposalF
)
from bims.models import TaxonGroupTaxonomy

User = get_user_model()


class UpdateTaxonTest(FastTenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.expert_user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.normal_user = User.objects.create_user('normal_user',
                                                    'normal_user@example.com',
                                                    'password')
        self.superuser = User.objects.create_user(
            username='superuser',
            email='superuser@example.com',
            password='password',
            is_superuser=True
        )
        self.taxonomy = TaxonomyF.create(
            scientific_name='Test Name',
            canonical_name='Test Canonical Name')
        self.taxon_group = TaxonGroupF.create(
            name='Test Group',
            taxonomies=(self.taxonomy,),
            experts=(self.expert_user,)
        )

    def test_expert_propose_update_taxon(self):
        self.client.login(username='testuser', password='password')

        url = reverse('update-taxon',
                      kwargs={
                          'taxon_id': self.taxonomy.pk,
                          'taxon_group_id': self.taxon_group.pk
                      })

        data = {
            'scientific_name': 'Updated Test Name',
            'canonical_name': 'Updated Test Canonical Name',
        }

        response = self.client.put(url, data, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        self.assertTrue(TaxonomyUpdateProposal.objects.exists())

        proposal = TaxonomyUpdateProposal.objects.first()
        self.assertEqual(proposal.scientific_name, 'Updated Test Name')
        self.assertEqual(proposal.canonical_name, 'Updated Test Canonical Name')
        self.assertEqual(proposal.status, 'pending')
        self.assertEqual(proposal.original_taxonomy, self.taxonomy)

        self.client.logout()

    def test_non_expert_propose_taxon_update(self):
        self.client.login(username='normal_user', password='password')

        url = reverse('update-taxon',
                      kwargs={
                          'taxon_id': self.taxonomy.pk,
                          'taxon_group_id': self.taxon_group.pk
                      })

        response = self.client.put(url, {}, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_superuser_propose_taxon_update(self):
        self.client.login(username='superuser', password='password')

        url = reverse('update-taxon',
                      kwargs={
                          'taxon_id': self.taxonomy.pk,
                          'taxon_group_id': self.taxon_group.pk
                      })

        response = self.client.put(url, {}, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.client.logout()

    def test_propose_taxon_update_in_pending(self):
        TaxonomyUpdateProposalF.create(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            status='pending'
        )
        self.client.login(username='normal_user', password='password')

        url = reverse('update-taxon',
                      kwargs={
                          'taxon_id': self.taxonomy.pk,
                          'taxon_group_id': self.taxon_group.pk
                      })

        response = self.client.put(url, {}, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_update_synonym_adds_accepted_name_to_group(self):
        """
        When updating a taxon to change it to a synonym,
        the accepted taxonomy should automatically be added to the group.
        """
        self.client.login(username='testuser', password='password')

        # Create an accepted taxonomy not yet in the group
        accepted_taxonomy = TaxonomyF.create(
            canonical_name='Accepted Name',
            scientific_name='Accepted Name',
            rank='species',
            taxonomic_status='ACCEPTED'
        )

        # Verify the accepted taxonomy is NOT in the group
        self.assertFalse(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists()
        )

        # Update the taxonomy to make it a synonym
        url = reverse('update-taxon',
                      kwargs={
                          'taxon_id': self.taxonomy.pk,
                          'taxon_group_id': self.taxon_group.pk
                      })

        data = {
            'taxonomic_status': 'SYNONYM',
            'accepted_taxonomy': accepted_taxonomy.pk,
        }

        response = self.client.put(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # Verify the accepted taxonomy was automatically added to the group
        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists(),
            "Accepted taxonomy should be automatically added when taxon becomes synonym"
        )

        self.client.logout()

    def test_create_proposal_for_synonym_adds_accepted_name(self):
        """
        Test that create_taxon_proposal automatically adds accepted taxonomy to group.
        """
        from bims.api_views.taxon_update import create_taxon_proposal

        # Create an accepted taxonomy
        accepted_taxonomy = TaxonomyF.create(
            canonical_name='Another Accepted',
            scientific_name='Another Accepted',
            rank='species',
            taxonomic_status='ACCEPTED'
        )

        # Create a new taxon that will be marked as synonym
        new_taxon = TaxonomyF.create(
            canonical_name='New Synonym',
            scientific_name='New Synonym',
            rank='species',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted_taxonomy
        )

        # Add to taxon group
        self.taxon_group.taxonomies.add(new_taxon)

        # Verify accepted not in group yet
        self.assertFalse(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists()
        )

        # Create proposal
        proposal = create_taxon_proposal(
            taxon=new_taxon,
            taxon_group=self.taxon_group,
            data={'taxonomic_status': 'SYNONYM'},
            creator=self.expert_user
        )

        self.assertIsNotNone(proposal)

        # Verify accepted taxonomy was automatically added
        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists(),
            "create_taxon_proposal should add accepted taxonomy to group"
        )

    def test_create_proposal_uses_original_taxon_import_date_for_created_at(self):
        """
        create_taxon_proposal should set created_at from the original taxon's
        import_date, not the current time.
        """
        from bims.api_views.taxon_update import create_taxon_proposal

        origin_date = datetime.date(2020, 5, 15)
        taxon = TaxonomyF.create(
            scientific_name='Date Test Taxon',
            canonical_name='Date Test Taxon',
            import_date=origin_date,
        )
        self.taxon_group.taxonomies.add(taxon)

        proposal = create_taxon_proposal(
            taxon=taxon,
            taxon_group=self.taxon_group,
            creator=self.expert_user,
        )

        self.assertIsNotNone(proposal.created_at)
        self.assertEqual(proposal.created_at.date(), origin_date)

    def test_create_proposal_sets_last_modified_by_to_creator(self):
        """
        create_taxon_proposal should set last_modified_by to the creator.
        """
        from bims.api_views.taxon_update import create_taxon_proposal

        taxon = TaxonomyF.create(
            scientific_name='Creator Test Taxon',
            canonical_name='Creator Test Taxon',
        )
        self.taxon_group.taxonomies.add(taxon)

        proposal = create_taxon_proposal(
            taxon=taxon,
            taxon_group=self.taxon_group,
            creator=self.expert_user,
        )

        self.assertEqual(proposal.last_modified_by, self.expert_user)

    def test_update_proposal_sets_last_modified_by(self):
        """
        update_taxon_proposal should update last_modified_by to the given user.
        """
        from bims.api_views.taxon_update import create_taxon_proposal, update_taxon_proposal

        taxon = TaxonomyF.create(
            scientific_name='Modifier Test Taxon',
            canonical_name='Modifier Test Taxon',
        )
        self.taxon_group.taxonomies.add(taxon)

        proposal = create_taxon_proposal(
            taxon=taxon,
            taxon_group=self.taxon_group,
            creator=self.expert_user,
        )
        self.assertEqual(proposal.last_modified_by, self.expert_user)

        update_taxon_proposal(
            proposal=proposal,
            data={'canonical_name': 'Modified Name'},
            user=self.normal_user,
        )

        proposal.refresh_from_db()
        self.assertEqual(proposal.last_modified_by, self.normal_user)

    def test_update_proposal_via_api_sets_last_modified_by(self):
        """
        PUT update-taxon should record request.user as last_modified_by when
        updating an existing pending proposal.
        """
        # First create a proposal
        TaxonomyUpdateProposalF.create(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            taxon_group_under_review=self.taxon_group,
            status='pending',
            collector_user=self.expert_user,
        )

        self.client.login(username='testuser', password='password')
        url = reverse('update-taxon', kwargs={
            'taxon_id': self.taxonomy.pk,
            'taxon_group_id': self.taxon_group.pk,
        })
        response = self.client.put(
            url,
            {'canonical_name': 'Second Edit'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        proposal = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            status='pending',
        ).first()
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.last_modified_by, self.expert_user)

    def test_proposal_last_modified_property_returns_updated_at(self):
        """
        TaxonomyUpdateProposal.last_modified property should return the
        raw updated_at datetime so the template can format it consistently.
        """
        proposal = TaxonomyUpdateProposalF.create(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
        )
        self.assertEqual(proposal.last_modified, proposal.updated_at)

    def test_proposal_created_at_not_overwritten_on_update(self):
        """
        Updating a proposal should not change its created_at.
        """
        from bims.api_views.taxon_update import create_taxon_proposal, update_taxon_proposal

        origin_date = datetime.date(2019, 3, 10)
        taxon = TaxonomyF.create(
            scientific_name='Stable CreatedAt Taxon',
            canonical_name='Stable CreatedAt Taxon',
            import_date=origin_date,
        )
        self.taxon_group.taxonomies.add(taxon)

        proposal = create_taxon_proposal(
            taxon=taxon,
            taxon_group=self.taxon_group,
            creator=self.expert_user,
        )
        original_created_at = proposal.created_at

        update_taxon_proposal(
            proposal=proposal,
            data={'canonical_name': 'Changed Name'},
            user=self.normal_user,
        )

        proposal.refresh_from_db()
        self.assertEqual(proposal.created_at, original_created_at)

    def test_create_proposal_does_not_overwrite_created_at_on_existing_pending(self):
        """
        If a pending proposal already exists, calling create_taxon_proposal
        again should update data fields but leave created_at unchanged.
        """
        from bims.api_views.taxon_update import create_taxon_proposal

        origin_date = datetime.date(2018, 6, 1)
        taxon = TaxonomyF.create(
            scientific_name='Existing Pending Taxon',
            canonical_name='Existing Pending Taxon',
            import_date=origin_date,
        )
        self.taxon_group.taxonomies.add(taxon)

        # First call creates the proposal and sets created_at from import_date
        proposal_first = create_taxon_proposal(
            taxon=taxon,
            taxon_group=self.taxon_group,
            creator=self.expert_user,
        )
        first_created_at = proposal_first.created_at
        self.assertIsNotNone(first_created_at)
        self.assertEqual(first_created_at.date(), origin_date)

        # Second call hits the existing pending proposal — created_at must not change
        proposal_second = create_taxon_proposal(
            taxon=taxon,
            taxon_group=self.taxon_group,
            creator=self.normal_user,
        )
        self.assertEqual(proposal_first.id, proposal_second.id)
        proposal_second.refresh_from_db()
        self.assertEqual(proposal_second.created_at, first_created_at)

    def test_reject_does_not_update_last_modified_by(self):
        """
        Rejecting a proposal should not change last_modified_by.
        """
        from bims.api_views.taxon_update import create_taxon_proposal, update_taxon_proposal

        taxon = TaxonomyF.create(
            scientific_name='Reject Test Taxon',
            canonical_name='Reject Test Taxon',
        )
        self.taxon_group.taxonomies.add(taxon)

        proposal = create_taxon_proposal(
            taxon=taxon,
            taxon_group=self.taxon_group,
            creator=self.expert_user,
        )
        # Editor modifies the proposal
        update_taxon_proposal(
            proposal=proposal,
            data={'canonical_name': 'Editor Edit'},
            user=self.normal_user,
        )
        proposal.refresh_from_db()
        self.assertEqual(proposal.last_modified_by, self.normal_user)

        # Superuser rejects — last_modified_by must remain the editor
        proposal.reject_data(self.superuser, comments='Not acceptable')

        proposal.refresh_from_db()
        self.assertEqual(proposal.status, 'rejected')
        self.assertEqual(
            proposal.last_modified_by,
            self.normal_user,
            'reject_data must not overwrite last_modified_by',
        )

    def test_taxonomy_created_at_property_returns_import_date(self):
        """
        Taxonomy.created_at_date should return import_date so the edit form
        displays the correct origin date for both Taxonomy and
        TaxonomyUpdateProposal objects via a single template variable.
        """
        import_date = datetime.date(2021, 7, 20)
        taxon = TaxonomyF.create(
            scientific_name='CreatedAt Property Test',
            canonical_name='CreatedAt Property Test',
            import_date=import_date,
        )
        self.assertEqual(taxon.created_at_date, import_date)

    def test_edit_form_created_at_uses_proposal_created_at_not_import_date(self):
        """
        When the edit form object is a TaxonomyUpdateProposal,
        proposal.created_at (a DB field inherited from AbstractTaxonomy) must
        store the original taxon's import_date — NOT the proposal's own
        import_date, which defaults to today.
        Note: the template renders object.created_at_date.  For Taxonomy that
        returns import_date; for TaxonomyUpdateProposal it returns the
        proposal's own import_date (today).  The authoritative creation-date
        for a proposal is stored in proposal.created_at.
        """
        from bims.api_views.taxon_update import create_taxon_proposal

        import_date = datetime.date(2017, 11, 5)
        taxon = TaxonomyF.create(
            scientific_name='Form CreatedAt Test',
            canonical_name='Form CreatedAt Test',
            import_date=import_date,
        )
        self.taxon_group.taxonomies.add(taxon)

        proposal = create_taxon_proposal(
            taxon=taxon,
            taxon_group=self.taxon_group,
            creator=self.expert_user,
        )

        # proposal.import_date defaults to today — different from original
        self.assertNotEqual(proposal.import_date, import_date)

        # proposal.created_at (DB field) holds the original taxon's import_date
        self.assertIsNotNone(proposal.created_at)
        self.assertEqual(proposal.created_at.date(), import_date)
