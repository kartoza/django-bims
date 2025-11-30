from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from unittest.mock import patch

from bims.tests.model_factories import TaxonomyF, TaxonGroupF, UserF, IUCNStatusF
from bims.models import Taxonomy, TaxonGroupTaxonomy


def mock_update_taxonomy_from_gbif(key, fetch_parent=True, get_vernacular=True):
    iucn_status = IUCNStatusF.create()
    taxonomy = TaxonomyF.create(
        gbif_key=key,
        scientific_name="Mocked Scientific Name",
        canonical_name="Mocked Canonical Name",
        iucn_status=iucn_status
    )
    return taxonomy


class AddNewTaxonTestCase(FastTenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.user = UserF.create(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.taxon_group = TaxonGroupF.create(
            name='test'
        )
        self.taxonomy = TaxonomyF()

    @patch('bims.api_views.taxon.update_taxonomy_from_gbif', side_effect=mock_update_taxonomy_from_gbif)
    def test_add_new_taxon_with_gbif_key(self, mock_update):
        data = {
            'gbifKey': '1',
            'taxonName': 'Test Taxon',
            'taxonGroup': self.taxon_group.name,
            'rank': 'species',
            'authorName': 'Test Author',
        }
        response = self.client.post(reverse('add-new-taxon'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id' in response.data)
        self.assertTrue('taxon_name' in response.data)
        self.assertEqual(response.data['taxon_name'], 'Mocked Canonical Name')

    @patch('bims.api_views.taxon.update_taxonomy_from_gbif', side_effect=mock_update_taxonomy_from_gbif)
    def test_add_new_taxon_without_gbif_key(self, mock_update):
        data = {
            'taxonName': 'Test Taxon Without GBIF',
            'taxonGroup': self.taxon_group.name,
            'rank': 'species',
            'parentId': self.taxonomy.id,
            'authorName': 'Test Author Without GBIF',
        }
        response = self.client.post(reverse('add-new-taxon'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id' in response.data)
        self.assertTrue('taxon_name' in response.data)
        self.assertEqual(response.data['taxon_name'], 'Test Taxon Without GBIF')

        data = {
            'taxonName': 'Test Taxon Without GBIF 2',
            'taxonGroupId': self.taxon_group.id,
            'rank': 'species',
            'familyId': self.taxonomy.id,
            'authorName': 'Test Author Without GBIF 2',
        }
        response = self.client.post(reverse('add-new-taxon'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id' in response.data)
        self.assertTrue('taxon_name' in response.data)
        self.assertEqual(response.data['taxon_name'], 'Test Taxon Without GBIF 2')

    def test_add_new_manual_taxon_reuses_existing_taxonomy(self):
        """
        When a manual taxon (no gbifKey) with the same canonical_name already exists,
        the API should reuse the existing Taxonomy instead of creating a duplicate.
        """
        existing = TaxonomyF.create(
            canonical_name="Manual Duplicate Taxon",
            scientific_name="Manual Duplicate Taxon",
            rank="species",
        )

        data = {
            "taxonName": "Manual Duplicate Taxon",
            "taxonGroup": self.taxon_group.name,
            "rank": "species",
            "authorName": "Some Author",
        }
        response = self.client.post(reverse("add-new-taxon"), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("id", response.data)
        self.assertIn("taxon_name", response.data)

        # Should reuse the existing taxonomy
        self.assertEqual(response.data["id"], existing.id)
        self.assertEqual(response.data["taxon_name"], existing.canonical_name)

        # And not create a second Taxonomy row with the same name
        self.assertEqual(
            Taxonomy.objects.filter(
                canonical_name__iexact="Manual Duplicate Taxon"
            ).count(),
            1,
        )

    def test_add_synonym_automatically_adds_accepted_name_to_group(self):
        """
        When a synonym is manually added to a taxon group,
        the accepted taxonomy should automatically be added to the same group.
        """
        # Create an accepted taxonomy
        accepted_taxonomy = TaxonomyF.create(
            canonical_name="Accepted Species",
            scientific_name="Accepted Species",
            rank="species",
            taxonomic_status="ACCEPTED"
        )

        # Create a synonym that references the accepted taxonomy
        synonym_taxonomy = TaxonomyF.create(
            canonical_name="Synonym Species",
            scientific_name="Synonym Species",
            rank="species",
            taxonomic_status="SYNONYM",
            accepted_taxonomy=accepted_taxonomy
        )

        # Verify the accepted taxonomy is NOT in the taxon group yet
        self.assertFalse(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists()
        )

        # Add the synonym to the taxon group
        data = {
            'taxonName': synonym_taxonomy.canonical_name,
            'taxonGroup': self.taxon_group.name,
            'rank': 'species',
        }
        response = self.client.post(reverse('add-new-taxon'), data)
        self.assertEqual(response.status_code, 200)

        # Verify the synonym was added to the group
        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=synonym_taxonomy,
                taxongroup=self.taxon_group
            ).exists()
        )

        # Verify the accepted taxonomy was AUTOMATICALLY added to the group
        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists(),
            "Accepted taxonomy should be automatically added when synonym is added"
        )

        # Verify it's marked as not validated (initial state)
        accepted_in_group = TaxonGroupTaxonomy.objects.get(
            taxonomy=accepted_taxonomy,
            taxongroup=self.taxon_group
        )
        self.assertFalse(accepted_in_group.is_validated)

    def test_add_synonym_when_accepted_already_in_group(self):
        """
        When a synonym is added and the accepted taxonomy is already in the group,
        it should not create a duplicate or error.
        """
        # Create an accepted taxonomy
        accepted_taxonomy = TaxonomyF.create(
            canonical_name="Already Present Accepted",
            scientific_name="Already Present Accepted",
            rank="species",
            taxonomic_status="ACCEPTED"
        )

        # Add the accepted taxonomy to the group first
        self.taxon_group.taxonomies.add(
            accepted_taxonomy,
            through_defaults={'is_validated': True}
        )

        # Create a synonym that references the accepted taxonomy
        synonym_taxonomy = TaxonomyF.create(
            canonical_name="Synonym Of Present",
            scientific_name="Synonym Of Present",
            rank="species",
            taxonomic_status="SYNONYM",
            accepted_taxonomy=accepted_taxonomy
        )

        # Add the synonym to the taxon group
        data = {
            'taxonName': synonym_taxonomy.canonical_name,
            'taxonGroup': self.taxon_group.name,
            'rank': 'species',
        }
        response = self.client.post(reverse('add-new-taxon'), data)
        self.assertEqual(response.status_code, 200)

        # Verify there's still only ONE entry for the accepted taxonomy
        self.assertEqual(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).count(),
            1,
            "Should not create duplicate entry for accepted taxonomy"
        )

    def test_add_non_synonym_does_not_add_extra_taxa(self):
        """
        When a non-synonym (accepted name) is added,
        it should not try to add any additional taxa.
        """
        # Create an accepted taxonomy
        accepted_taxonomy = TaxonomyF.create(
            canonical_name="Regular Accepted",
            scientific_name="Regular Accepted",
            rank="species",
            taxonomic_status="ACCEPTED",
            accepted_taxonomy=None  # No accepted taxonomy (it IS the accepted name)
        )

        # Count existing taxa in group before
        initial_count = TaxonGroupTaxonomy.objects.filter(
            taxongroup=self.taxon_group
        ).count()

        # Add the accepted taxonomy to the group
        data = {
            'taxonName': accepted_taxonomy.canonical_name,
            'taxonGroup': self.taxon_group.name,
            'rank': 'species',
        }
        response = self.client.post(reverse('add-new-taxon'), data)
        self.assertEqual(response.status_code, 200)

        # Verify only ONE taxon was added (the one we requested)
        final_count = TaxonGroupTaxonomy.objects.filter(
            taxongroup=self.taxon_group
        ).count()
        self.assertEqual(
            final_count,
            initial_count + 1,
            "Should only add the requested taxon, not any additional taxa"
        )
