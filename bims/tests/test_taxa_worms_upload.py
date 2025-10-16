# bims/tests/test_worms_taxa_upload.py
import os
import json

from django.core.files import File
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from mock import mock

from bims.models import TaxonGroupTaxonomy
from bims.tests.model_factories import (
    UploadSessionF,
    TaxonGroupF,
    UserF,
)
from bims.models import Taxonomy
from bims.scripts.taxa_upload_worms import WormsTaxaCSVUpload

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data'
)


class TestWormsTaxaUpload(FastTenantTestCase):

    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.taxon_group = TaxonGroupF.create()
        self.owner = UserF.create(first_name='tester')

        with open(os.path.join(
            test_data_directory, 'worms_sample.csv'
        ), 'rb') as file:
            self.upload_session = UploadSessionF.create(
                uploader=self.owner,
                process_file=File(file),
                module_group=self.taxon_group
            )

    @mock.patch('bims.scripts.data_upload.DataCSVUpload.finish')
    @mock.patch('bims.scripts.taxa_upload_worms.preferences')
    def test_worms_upload_validated(self, mock_preferences, mock_finish):
        mock_finish.return_value = None
        mock_preferences.SiteSetting.auto_validate_taxa_on_upload = True

        uploader = WormsTaxaCSVUpload()
        uploader.upload_session = self.upload_session
        uploader.start('cp1252')

        self.assertEqual(uploader.error_list, [])

        # Species created with proper rank and author
        sp = Taxonomy.objects.get(
            canonical_name='[non-Uristidae] albinus',
            rank='SPECIES',
        )
        self.assertIn('1932', (sp.author or ''))
        self.assertIsNotNone(sp.parent)
        self.assertEqual(sp.parent.canonical_name, '[non-Uristidae]')
        self.assertEqual(sp.parent.rank, 'GENUS')

        # Marine habitat tag attached
        self.assertTrue(
            sp.tags.filter(name='Marine').exists()
        )

        # Source reference (citation) saved
        self.assertIsNotNone(sp.source_reference)
        self.assertIn('marinespecies.org', (sp.source_reference.note or ''))

        # Added to group as validated
        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=sp,
                taxongroup=self.taxon_group,
                is_validated=True
            ).exists()
        )

        # Subfamily row produces SUBFAMILY with FAMILY parent
        subfam = Taxonomy.objects.get(
            canonical_name='[unassigned] Cypraeidae',
            rank='SUBFAMILY',
        )
        self.assertIsNotNone(subfam.parent)
        self.assertEqual(subfam.parent.canonical_name, 'Cypraeidae')
        self.assertEqual(subfam.parent.rank, 'FAMILY')

        # Temporary name mapped
        temp_tax = Taxonomy.objects.get(
            canonical_name='[unassigned] Decapodiformes',
            rank='ORDER',
        )
        self.assertEqual(temp_tax.taxonomic_status, 'TEMPORARY NAME')

        # Accepted species has ACCEPTED status and no accepted_taxonomy link
        accepted = Taxonomy.objects.get(
            canonical_name='[non-Uristidae] dawsoni',
            rank='SPECIES',
        )
        self.assertEqual(accepted.taxonomic_status, 'ACCEPTED')
        self.assertIsNone(accepted.accepted_taxonomy)

        # Alternative representation -> synonym + accepted link created
        alt_rep = Taxonomy.objects.get(
            canonical_name='“Montereina” aurea',
            rank='SPECIES',
        )
        self.assertEqual(alt_rep.taxonomic_status, 'SYNONYM')
        self.assertIsNotNone(alt_rep.accepted_taxonomy)
        self.assertEqual(alt_rep.accepted_taxonomy.canonical_name, 'Peltodoris aurea')

        acostitrapa = Taxonomy.objects.filter(
            canonical_name='×Acostitrapa',
            rank='GENUS'
        )
        self.assertTrue(acostitrapa.exists())

        # Additional data keeps AphiaID (and other columns)
        extras = alt_rep.additional_data
        self.assertIn('AphiaID', extras)

        # Terrestrial-only -> Terrestrial tag present
        terr = Taxonomy.objects.get(
            canonical_name='[unassigned] Scolodontidae',
            rank='SUBFAMILY',
        )
        self.assertTrue(terr.tags.filter(name='Terrestrial').exists())

    @mock.patch('bims.scripts.data_upload.DataCSVUpload.finish')
    @mock.patch('bims.scripts.taxa_upload_worms.preferences')
    def test_worms_upload_unvalidated(self, mock_preferences, mock_finish):
        mock_finish.return_value = None
        mock_preferences.SiteSetting.auto_validate_taxa_on_upload = False

        with open(os.path.join(
            test_data_directory, 'worms_sample.csv'
        ), 'rb') as file:
            upload_session = UploadSessionF.create(
                uploader=self.owner,
                process_file=File(file),
                module_group=self.taxon_group
            )

        uploader = WormsTaxaCSVUpload()
        uploader.upload_session = upload_session
        uploader.start('utf-8')

        self.assertEqual(uploader.error_list, [])

        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy__canonical_name='[non-Uristidae] albinus',
                taxongroup=self.taxon_group,
                is_validated=False
            ).exists()
        )

    @mock.patch('bims.scripts.data_upload.DataCSVUpload.finish')
    @mock.patch('bims.scripts.taxa_upload_worms.preferences')
    def test_worms_parent_reuse(self, mock_preferences, mock_finish):
        mock_finish.return_value = None
        mock_preferences.SiteSetting.auto_validate_taxa_on_upload = True

        uploader = WormsTaxaCSVUpload()
        uploader.upload_session = self.upload_session
        uploader.start('utf-8')

        self.assertEqual(uploader.error_list, [])

        albinus = Taxonomy.objects.get(
            canonical_name='[non-Uristidae] albinus',
            rank='SPECIES',
        )
        dawsoni = Taxonomy.objects.get(
            canonical_name='[non-Uristidae] dawsoni',
            rank='SPECIES',
        )
        self.assertIsNotNone(albinus.parent)
        self.assertEqual(albinus.parent_id, dawsoni.parent_id)
        self.assertEqual(albinus.parent.canonical_name, '[non-Uristidae]')
        self.assertEqual(albinus.parent.rank, 'GENUS')
