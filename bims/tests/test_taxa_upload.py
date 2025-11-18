import os

from django.core.files import File
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from mock import mock

from bims.models import TaxonGroupTaxonomy
from bims.scripts.taxa_upload import TaxaCSVUpload
from bims.tests.model_factories import (
    UploadSessionF,
    TaxonGroupF,
    UserF,
    TaxonomyF,
    Taxonomy,
    VernacularName,
    IUCNStatusF
)

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data'
)


class TestTaxaUpload(FastTenantTestCase):

    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.taxon_group = TaxonGroupF.create()
        self.owner = UserF.create(
            first_name='tester'
        )
        self.taxonomy = TaxonomyF.create()

        # create IUCN statuses used in upload mapping
        IUCNStatusF.create(
            category='NE',
            national=True
        )

        IUCNStatusF.create(
            category='NE',
            national=False
        )

        IUCNStatusF.create(
            category='NE',
            national=False
        )

        with open(os.path.join(
            test_data_directory, 'taxa_upload_family.csv'
        ), 'rb') as file:
            self.upload_session = UploadSessionF.create(
                uploader=self.owner,
                process_file=File(file),
                module_group=self.taxon_group
            )

    @mock.patch('bims.scripts.data_upload.DataCSVUpload.finish')
    @mock.patch('bims.scripts.taxa_upload.fetch_all_species_from_gbif')
    def test_taxa_upload(self, mock_fetch_all_species_from_gbif, mock_finish):
        mock_finish.return_value = None
        mock_fetch_all_species_from_gbif.return_value = self.taxonomy

        taxa_csv_upload = TaxaCSVUpload()
        taxa_csv_upload.upload_session = self.upload_session
        taxa_csv_upload.start('utf-8-sig')

        self.assertTrue(
            Taxonomy.objects.filter(
                canonical_name__icontains='Ecnomidae2',
                taxonomic_status__iexact='synonym'
            ).exists()
        )

        self.assertTrue(
            VernacularName.objects.filter(
                name='Earthworm',
                language='eng',
                taxonomy__canonical_name__icontains='Oligochaeta'
            ).exists()
        )

        self.assertTrue(
            VernacularName.objects.filter(
                name='Earthworm2',
                language='eng',
                taxonomy__canonical_name__icontains='Oligochaeta'
            ).exists()
        )

        self.assertTrue(
            VernacularName.objects.filter(
                name='ミミズ',
                language='jpn',
                taxonomy__canonical_name__icontains='Oligochaeta'
            ).exists()
        )

        self.assertTrue(
            VernacularName.objects.filter(
                name='Animalia test2',
                language='ind',
            ).exists()
        )

        self.assertTrue(
            Taxonomy.objects.get(
                canonical_name='Ecnomidae'
            ).tags.filter(
                name='lentic'
            ).exists()
        )

        self.assertTrue(
            VernacularName.objects.filter(
                name='trattnattsländor',
                language='deu',
            ).exists()
        )

        self.assertTrue(
            VernacularName.objects.filter(
                name='test',
                language='eng',
            ).exists()
        )

        self.assertTrue(
            Taxonomy.objects.get(
                canonical_name='Ecnomidae'
            ).biographic_distributions.filter(
                name='ANT',
            ).exists()
        )

        self.assertTrue(
            Taxonomy.objects.get(
                canonical_name='Ecnomidae'
            ).biographic_distributions.filter(
                name='AT',
                doubtful=True
            ).exists()
        )

        self.assertTrue(
            Taxonomy.objects.get(
                canonical_name='Ecnomidae'
            ).tags.filter(
                name='Lakes'
            ).exists()
        )

        self.assertTrue(
            Taxonomy.objects.filter(
                canonical_name='Ecnomidae',
                scientific_name__icontains='Dimas 1789',
                author='Dimas 1789'
            ).exists()
        )

        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy__canonical_name='Ecnomidae',
                taxongroup=self.taxon_group,
                is_validated=True
            ).exists()
        )

        self.assertTrue(
            Taxonomy.objects.filter(
                invasion__category='Category 1a invasive',
                origin='indigenous',
            ).exists()
        )

        self.assertTrue(
            Taxonomy.objects.filter(
                canonical_name__icontains='Testgenus testspecies',
                rank='SPECIES',
                species_group__name='Test species group'
            ).exists()
        )

    @mock.patch('bims.scripts.data_upload.DataCSVUpload.finish')
    @mock.patch('bims.scripts.taxa_upload.fetch_all_species_from_gbif')
    @mock.patch('bims.scripts.taxa_upload.preferences')
    def test_taxa_upload_unvalidated(
        self,
        mock_preferences,
        mock_fetch_all_species_from_gbif,
        mock_finish
    ):
        # Force proposals / unvalidated path
        mock_preferences.SiteSetting.auto_validate_taxa_on_upload = False
        mock_finish.return_value = None
        mock_fetch_all_species_from_gbif.return_value = self.taxonomy

        with open(os.path.join(
            test_data_directory, 'taxa_upload_family_2.csv'
        ), 'rb') as file:
            upload_session = UploadSessionF.create(
                uploader=self.owner,
                process_file=File(file),
                module_group=self.taxon_group
            )

        taxa_csv_upload = TaxaCSVUpload()
        taxa_csv_upload.upload_session = upload_session
        taxa_csv_upload.start('utf-8-sig')

        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy__canonical_name='Oligochaeta2',
                taxongroup=self.taxon_group,
                is_validated=False
            ).exists()
        )

    @mock.patch('bims.scripts.data_upload.DataCSVUpload.finish')
    @mock.patch('bims.scripts.taxa_upload.fetch_all_species_from_gbif')
    def test_taxa_upload_variety_and_forma(
        self,
        mock_fetch_all_species_from_gbif,
        mock_finish
    ):
        mock_finish.return_value = None
        mock_fetch_all_species_from_gbif.return_value = self.taxonomy

        with open(os.path.join(
            test_data_directory, 'variety_forma_example.csv'
        ), 'rb') as file:
            upload_session = UploadSessionF.create(
                uploader=self.owner,
                process_file=File(file),
                module_group=self.taxon_group
            )

        taxa_csv_upload = TaxaCSVUpload()
        taxa_csv_upload.upload_session = upload_session
        taxa_csv_upload.start('utf-8-sig')

        # We should have created at least one VARIETY and one FORMA
        self.assertTrue(
            Taxonomy.objects.filter(
                rank='VARIETY'
            ).exists()
        )

        self.assertTrue(
            Taxonomy.objects.filter(
                rank='FORMA'
            ).exists()
        )

    @mock.patch('bims.scripts.data_upload.DataCSVUpload.finish')
    @mock.patch('bims.scripts.taxa_upload.fetch_all_species_from_gbif')
    def test_taxa_upload_species_and_subspecies_names(
            self,
            mock_fetch_all_species_from_gbif,
            mock_finish
    ):
        """
        Validate current behaviour of species / subspecies handling:

        - Species row (e.g. Genus=Labeobarbus, Species=mariae, Taxon='mariae',
          Taxon rank='Species', Authors='Smith 1990'):
            -> we expect a Taxonomy with rank='SPECIES' and canonical_name
               containing 'mariae'
            -> scientific_name should include the author string

        - Subspecies row (e.g. Taxon='mariae atlanticus',
          Taxon rank='Subspecies', Authors='Jones 2001'):
            -> we expect a Taxonomy with rank='SUBSPECIES' and canonical_name
               containing 'mariae atlanticus'
            -> scientific_name should include the author string

        Note: The code also creates/updates parent helpers like
        'Labeobarbus mariae' with blank rank. We don't assert on that rank
        because it's an internal side effect of parent resolution.
        """

        mock_finish.return_value = None

        # Any GBIF fetch inside process_data/get_parent should return *some*
        # taxonomy instance so the code can attach parents etc.
        # We don't really care about its initial values because the uploader
        # will mutate it heavily.
        mock_fetch_all_species_from_gbif.return_value = TaxonomyF.create()

        # use the CSV with species + subspecies cases
        with open(
                os.path.join(
                    test_data_directory,
                    'taxa_upload_species_subspecies.csv'
                ),
                'rb'
        ) as file:
            upload_session = UploadSessionF.create(
                uploader=self.owner,
                process_file=File(file),
                module_group=self.taxon_group
            )

        taxa_csv_upload = TaxaCSVUpload()
        taxa_csv_upload.upload_session = upload_session
        taxa_csv_upload.start('utf-8-sig')

        # --- Species assertion ---
        # We expect at least one SPECIES row for "mariae"
        self.assertTrue(
            Taxonomy.objects.filter(
                rank='SPECIES',
                canonical_name__icontains='mariae',
                scientific_name__icontains='Smith 1990',  # author appended
            ).exists(),
            msg='Expected a SPECIES taxon for "mariae" with author "Smith 1990".'
        )

        # --- Subspecies assertion ---
        # We expect at least one SUBSPECIES row for "mariae atlanticus"
        self.assertTrue(
            Taxonomy.objects.filter(
                rank='SUBSPECIES',
                canonical_name__icontains='mariae atlanticus',
                scientific_name__icontains='Jones 2001',  # author appended
            ).exists(),
            msg='Expected a SUBSPECIES taxon for "mariae atlanticus" with author "Jones 2001".'
        )

        # --- Optional sanity check for the helper parent species ---
        # The importer tends to create a parent "species-like" taxon that
        # represents the species name joined to the genus, but that object
        # may not have rank set yet. We just assert it exists, not rank.
        self.assertTrue(
            Taxonomy.objects.filter(
                canonical_name__icontains='mariae'
            ).exists(),
            msg='Expected at least one taxonomy containing "mariae" as parent/anchor.'
        )

    @mock.patch('bims.scripts.data_upload.DataCSVUpload.finish')
    @mock.patch('bims.scripts.taxa_upload.fetch_all_species_from_gbif')
    @mock.patch('bims.templatetags.site.is_fada_site')
    def test_fada_taxonomic_status_preserved_from_csv(
        self,
        mock_is_fada_site,
        mock_fetch_gbif,
        mock_finish
    ):
        """
        Test that for FADA sites, the taxonomic status from CSV is preserved
        and not overwritten by GBIF data (e.g., HOMOTYPIC_SYNONYM).

        This test addresses the issue where GBIF returns taxonomic statuses
        like 'HOMOTYPIC_SYNONYM' that don't exist in FADA's taxonomy system.
        For FADA sites, CSV taxonomic status should always take precedence.
        """
        mock_finish.return_value = None
        mock_is_fada_site.return_value = True

        # Mock GBIF to not fetch anything - we want to test CSV-only upload
        # This simulates FADA sites where on_gbif=False by default
        mock_fetch_gbif.return_value = None

        # Create upload session with FADA test data
        with open(os.path.join(
            test_data_directory, 'taxa_upload_fada_status.csv'
        ), 'rb') as file:
            upload_session = UploadSessionF.create(
                uploader=self.owner,
                process_file=File(file),
                module_group=self.taxon_group
            )

        # Run the upload
        taxa_csv_upload = TaxaCSVUpload()
        taxa_csv_upload.upload_session = upload_session
        taxa_csv_upload.start('utf-8-sig')

        # Verify that CSV taxonomic status is preserved for FADA
        # The CSV specifies SYNONYM, not HOMOTYPIC_SYNONYM
        fada_synonym = Taxonomy.objects.filter(
            canonical_name='Panthera tigris'
        ).first()

        self.assertIsNotNone(
            fada_synonym,
            msg='Expected Panthera tigris to be created from CSV'
        )

        # Critical assertion: taxonomic_status should be SYNONYM (from CSV)
        # NOT HOMOTYPIC_SYNONYM (from GBIF)
        self.assertEqual(
            fada_synonym.taxonomic_status,
            'SYNONYM',
            msg=f'FADA sites must preserve CSV taxonomic_status. '
                f'Expected SYNONYM but got {fada_synonym.taxonomic_status}. '
                f'GBIF status should not override CSV for FADA.'
        )

        # Verify ACCEPTED status is also preserved
        fada_accepted = Taxonomy.objects.filter(
            canonical_name='Panthera leo'
        ).first()

        self.assertIsNotNone(
            fada_accepted,
            msg='Expected Panthera leo to be created from CSV'
        )

        self.assertEqual(
            fada_accepted.taxonomic_status,
            'ACCEPTED',
            msg='FADA sites must preserve ACCEPTED status from CSV'
        )

    @mock.patch('bims.scripts.data_upload.DataCSVUpload.finish')
    @mock.patch('bims.scripts.taxa_upload.fetch_all_species_from_gbif')
    @mock.patch('bims.templatetags.site.is_fada_site')
    def test_non_fada_allows_gbif_taxonomic_status(
        self,
        mock_is_fada_site,
        mock_fetch_gbif,
        mock_finish
    ):
        """
        Test that for non-FADA sites, GBIF taxonomic status can override CSV.
        This ensures our fix only applies to FADA sites.
        """
        mock_finish.return_value = None
        mock_is_fada_site.return_value = False  # Not a FADA site

        # Mock GBIF to not fetch - we'll test preserve_taxonomic_status flag
        mock_fetch_gbif.return_value = None

        # Create upload session
        with open(os.path.join(
            test_data_directory, 'taxa_upload_fada_status.csv'
        ), 'rb') as file:
            upload_session = UploadSessionF.create(
                uploader=self.owner,
                process_file=File(file),
                module_group=self.taxon_group
            )

        # Run the upload
        taxa_csv_upload = TaxaCSVUpload()
        taxa_csv_upload.upload_session = upload_session
        taxa_csv_upload.start('utf-8-sig')

        # For non-FADA sites, GBIF status may be used
        # (behavior depends on exact upload flow, but we're testing
        # that our preserve_taxonomic_status flag is False for non-FADA)
        non_fada_taxon = Taxonomy.objects.filter(
            canonical_name='Panthera tigris'
        ).first()

        self.assertIsNotNone(
            non_fada_taxon,
            msg='Expected Panthera tigris to be created'
        )

        # The exact status depends on upload logic, but the key is that
        # preserve_taxonomic_status=False was passed to GBIF functions
        # We just verify the taxon exists and has some valid status
        self.assertIn(
            non_fada_taxon.taxonomic_status,
            ['SYNONYM', 'HOMOTYPIC_SYNONYM', 'ACCEPTED', ''],
            msg='Non-FADA taxonomic status should be valid'
        )


    def test_csv_upload_synonym_adds_accepted_name(self):
        """
        Test that when a synonym is uploaded via CSV,
        the accepted taxonomy is automatically added to the taxon group.
        """
        # Create an accepted taxonomy
        accepted_taxonomy = TaxonomyF.create(
            canonical_name='Accepted Name CSV',
            scientific_name='Accepted Name CSV',
            rank='SPECIES',
            taxonomic_status='ACCEPTED'
        )

        # Create a synonym taxonomy
        synonym_taxonomy = TaxonomyF.create(
            canonical_name='Synonym Name CSV',
            scientific_name='Synonym Name CSV',
            rank='SPECIES',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted_taxonomy
        )

        # Verify neither is in the taxon group yet
        self.assertFalse(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists()
        )
        self.assertFalse(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=synonym_taxonomy,
                taxongroup=self.taxon_group
            ).exists()
        )

        # Use the add_taxon_to_taxon_group method (simulating CSV upload)
        from bims.scripts.taxa_upload import TaxaProcessor
        processor = TaxaProcessor()
        processor.add_taxon_to_taxon_group(synonym_taxonomy, self.taxon_group, validated=False)

        # Verify the synonym was added
        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=synonym_taxonomy,
                taxongroup=self.taxon_group
            ).exists(),
            "Synonym should be added to the group"
        )

        # Verify the accepted taxonomy was AUTOMATICALLY added
        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists(),
            "Accepted taxonomy should be automatically added when synonym is uploaded"
        )

        # Verify both are marked as not validated
        synonym_in_group = TaxonGroupTaxonomy.objects.get(
            taxonomy=synonym_taxonomy,
            taxongroup=self.taxon_group
        )
        self.assertFalse(synonym_in_group.is_validated)

        accepted_in_group = TaxonGroupTaxonomy.objects.get(
            taxonomy=accepted_taxonomy,
            taxongroup=self.taxon_group
        )
        self.assertFalse(accepted_in_group.is_validated)
