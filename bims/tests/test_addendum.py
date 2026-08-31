from django.contrib.auth import get_user_model
from django_tenants.test.cases import FastTenantTestCase

from bims.api_views.taxon_update import (
    create_taxon_proposal,
    update_taxon_proposal,
)
from bims.enums.taxon_addendum import TaxonAddendum
from bims.models.taxonomy import Taxonomy
from bims.models.taxonomy_update_proposal import TaxonomyUpdateProposal
from bims.serializers.checklist_serializer import (
    ChecklistPDFSerializer,
    ChecklistSerializer,
)
from bims.serializers.coldp_serializer import ColDPTaxonSerializer
from bims.serializers.taxon_serializer import TaxonSerializer
from bims.tests.model_factories import TaxonGroupF, TaxonomyF
from bims.utils.taxonomy import build_name_with_addendum, get_addendum_display
from bims.views.download_csv_taxa_list import TaxaCSVSerializer

User = get_user_model()


class TestAddendumHelpers(FastTenantTestCase):

    def test_get_addendum_display_abbreviated(self):
        self.assertEqual(
            get_addendum_display(TaxonAddendum.SENSU_LATO.name, abbreviate=True),
            's.l.'
        )

    def test_get_addendum_display_full_text(self):
        self.assertEqual(
            get_addendum_display(TaxonAddendum.SENSU_LATO.name, abbreviate=False),
            'sensu lato'
        )

    def test_get_addendum_display_empty_code(self):
        self.assertEqual(get_addendum_display(''), '')
        self.assertEqual(get_addendum_display(None), '')

    def test_get_addendum_display_unknown_code(self):
        self.assertEqual(get_addendum_display('NOT_A_REAL_CODE'), '')

    def test_build_name_with_addendum(self):
        name = build_name_with_addendum(
            'Aquanothrus montanus',
            'Engelbrecht, 1975',
            TaxonAddendum.SENSU_LATO.name,
            abbreviate=True,
        )
        self.assertEqual(name, 'Aquanothrus montanus s.l. Engelbrecht, 1975')

    def test_build_name_with_addendum_no_code(self):
        name = build_name_with_addendum(
            'Aquanothrus montanus', 'Engelbrecht, 1975', '', abbreviate=True
        )
        self.assertEqual(name, 'Aquanothrus montanus Engelbrecht, 1975')


class TestAddendumModelField(FastTenantTestCase):

    def test_field_blank_by_default(self):
        taxon = TaxonomyF.create()
        self.assertEqual(taxon.addendum, '')

    def test_field_accepts_sensu_lato(self):
        taxon = TaxonomyF.create(addendum=TaxonAddendum.SENSU_LATO.name)
        taxon.refresh_from_db()
        self.assertEqual(taxon.addendum, TaxonAddendum.SENSU_LATO.name)

    def test_field_choices_contain_sensu_lato(self):
        choices = dict(Taxonomy._meta.get_field('addendum').choices)
        self.assertEqual(choices.get('SENSU_LATO'), 'sensu lato')


class TestAddendumSerializers(FastTenantTestCase):

    def setUp(self):
        self.taxon = TaxonomyF.create(
            scientific_name='Aquanothrus montanus Engelbrecht, 1975',
            canonical_name='Aquanothrus montanus',
            author='Engelbrecht, 1975',
            addendum=TaxonAddendum.SENSU_LATO.name,
        )
        self.plain_taxon = TaxonomyF.create(
            scientific_name='Homo sapiens L.',
            canonical_name='Homo sapiens',
            author='L.',
        )

    def test_checklist_pdf_serializer_appends_abbreviation(self):
        data = ChecklistPDFSerializer(self.taxon).data
        self.assertEqual(
            data['scientific_name'], 'Aquanothrus montanus s.l. Engelbrecht, 1975'
        )

    def test_checklist_pdf_serializer_no_addendum(self):
        data = ChecklistPDFSerializer(self.plain_taxon).data
        self.assertNotIn('s.l.', data['scientific_name'])

    def test_checklist_serializer_appends_abbreviation(self):
        data = ChecklistSerializer(self.taxon).data
        self.assertEqual(
            data['scientific_name'], 'Aquanothrus montanus s.l. Engelbrecht, 1975'
        )

    def test_checklist_serializer_no_addendum(self):
        data = ChecklistSerializer(self.plain_taxon).data
        self.assertEqual(data['scientific_name'], 'Homo sapiens L.')

    def test_coldp_name_phrase_set(self):
        data = ColDPTaxonSerializer(self.taxon).data
        self.assertEqual(data['namePhrase'], 'sensu lato')

    def test_coldp_name_phrase_empty(self):
        data = ColDPTaxonSerializer(self.plain_taxon).data
        self.assertEqual(data['namePhrase'], '')

    def test_taxa_csv_serializer_taxon_and_authority(self):
        serializer = TaxaCSVSerializer(self.taxon)
        data = serializer.data
        self.assertIn('s.l.', data['taxon'])
        self.assertEqual(
            data['scientific_name_and_authority'],
            'Aquanothrus montanus s.l. Engelbrecht, 1975'
        )
        self.assertEqual(data['addendum'], 'sensu lato')

    def test_taxa_csv_serializer_no_addendum(self):
        serializer = TaxaCSVSerializer(self.plain_taxon)
        data = serializer.data
        self.assertNotIn('s.l.', data['taxon'])
        self.assertEqual(data['addendum'], '')

    def test_taxon_serializer_addendum_and_scientific_name(self):
        data = TaxonSerializer(self.taxon, context={'validated': True}).data
        self.assertEqual(data['addendum'], 'sensu lato')
        self.assertIn('sensu lato', data['scientific_name'])

    def test_taxon_serializer_no_addendum(self):
        data = TaxonSerializer(self.plain_taxon, context={'validated': True}).data
        self.assertEqual(data['addendum'], '')
        self.assertEqual(data['scientific_name'], 'Homo sapiens L.')


class TestAddendumProposalLifecycle(FastTenantTestCase):

    def setUp(self):
        self.superuser = User.objects.create_user(
            username='superuser',
            email='superuser@example.com',
            password='password',
            is_superuser=True,
        )
        self.taxon = TaxonomyF.create(
            scientific_name='Test Name',
            canonical_name='Test Canonical Name',
        )
        self.taxon_group = TaxonGroupF.create(
            name='Test Group',
            taxonomies=(self.taxon,),
        )

    def test_create_proposal_carries_addendum(self):
        proposal = create_taxon_proposal(
            taxon=self.taxon,
            taxon_group=self.taxon_group,
            data={'addendum': TaxonAddendum.SENSU_LATO.name},
            creator=self.superuser,
        )
        self.assertEqual(proposal.addendum, TaxonAddendum.SENSU_LATO.name)

    def test_update_proposal_changes_addendum(self):
        proposal = create_taxon_proposal(
            taxon=self.taxon,
            taxon_group=self.taxon_group,
            data={'addendum': TaxonAddendum.SENSU_LATO.name},
            creator=self.superuser,
        )
        updated = update_taxon_proposal(
            proposal=proposal,
            data={'addendum': ''},
            user=self.superuser,
        )
        self.assertEqual(updated.addendum, '')

    def test_approve_copies_addendum_to_taxonomy(self):
        proposal = create_taxon_proposal(
            taxon=self.taxon,
            taxon_group=self.taxon_group,
            data={'addendum': TaxonAddendum.SENSU_LATO.name},
            creator=self.superuser,
        )
        proposal.approve(self.superuser, suppress_emails=True)

        self.taxon.refresh_from_db()
        self.assertEqual(self.taxon.addendum, TaxonAddendum.SENSU_LATO.name)

    def test_approve_without_addendum_leaves_it_blank(self):
        proposal = create_taxon_proposal(
            taxon=self.taxon,
            taxon_group=self.taxon_group,
            data={},
            creator=self.superuser,
        )
        proposal.approve(self.superuser, suppress_emails=True)

        self.taxon.refresh_from_db()
        self.assertEqual(self.taxon.addendum, '')
