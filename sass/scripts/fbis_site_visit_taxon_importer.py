from datetime import datetime
from django.db.models import signals
from django.db.utils import IntegrityError
from easyaudit.signals.model_signals import pre_save as easyaudit_presave
from geonode.people.models import Profile
from sass.models import SiteVisitTaxon, SiteVisit, SassTaxon, TaxonAbundance
from sass.scripts.fbis_importer import FbisImporter


class FbisSiteVisitTaxonImporter(FbisImporter):

    content_type_model = SiteVisitTaxon
    table_name = 'SiteVisitTaxon'
    success = 0
    failed = 0

    def start_processing_rows(self):
        signals.pre_save.disconnect(
            easyaudit_presave,
            dispatch_uid='easy_audit_signals_pre_save'
        )

    def finish_processing_rows(self):
        signals.pre_save.connect(
            easyaudit_presave,
            dispatch_uid='easy_audit_signals_pre_save'
        )
        print('Failed : %s' % self.failed)

    def process_row(self, row, index):

        site_visit = self.get_object_from_uuid(
            column='SiteVisitID',
            model=SiteVisit
        )

        sass_taxon = self.get_object_from_uuid(
            column='TaxonID',
            model=SassTaxon
        )

        taxon_abundance = self.get_object_from_uuid(
            column='TaxonAbundanceID',
            model=TaxonAbundance
        )

        collection_date = datetime.strptime(
            self.get_row_value('DateFrom'),
            '%m/%d/%y %H:%M:%S'
        )

        user_id = self.get_row_value('UserID')
        if not user_id:
            user_id = self.get_row_value('User')

        user = self.get_object_from_uuid(
            column='User',
            model=Profile,
            uuid=user_id
        )

        try:
            site_visit_taxon, status = SiteVisitTaxon.objects.get_or_create(
                site=site_visit.location_site,
                collection_date=collection_date,
                collector=user.username,
                owner=user,
                notes='From SASS',
                taxonomy=sass_taxon.taxon,
                institution_id='fbis',
                source_collection='fbis',
                taxon_abundance=taxon_abundance,
                site_visit=site_visit
            )
            site_visit_taxon.sass_taxon = sass_taxon
            site_visit_taxon.save()
        except (ValueError, IntegrityError, AttributeError):
            self.failed += 1
            print('Error')
            return

        self.save_uuid(
            uuid=self.get_row_value('SiteVisitTaxonID', row),
            object_id=site_visit_taxon.id
        )
