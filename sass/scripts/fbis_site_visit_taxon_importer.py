from bims.models import (
    FbisUUID,
)
from sass.models import SiteVisitTaxon, SiteVisit, SassTaxon, TaxonAbundance
from sass.scripts.fbis_importer import FbisImporter


class FbisSiteVisitTaxonImporter(FbisImporter):

    content_type_model = SiteVisitTaxon
    table_name = 'SiteVisitTaxon'

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
            self.get_row_value('SiteVisit'),
            '%m/%d/%y %H:%M:%S'
        ),

        # Get owner
        owner = None
        owners = FbisUUID.objects.filter(
            uuid=self.get_row_value('OwnerID', row)
        )
        if owners.exists():
            owner = owners[0].content_object

        river, created = River.objects.get_or_create(
            name=self.get_row_value('RiverName', row),
            owner=owner
        )
        river.validated = validated_value
        river.save()

        self.save_uuid(
            uuid=self.get_row_value('RiverID', row),
            object_id=river.id
        )
