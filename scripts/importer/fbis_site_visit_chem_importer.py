from sass.models import SiteVisitChem, SiteVisit, Chem
from scripts.importer.fbis_importer import FbisImporter


class FbisSiteVisitChemImporter(FbisImporter):

    content_type_model = SiteVisitChem
    table_name = 'SiteVisitChem'
    failed = 0
    added = 0

    def finish_processing_rows(self):
        print('Failed : %s' % self.failed)

    def process_row(self, row, index):
        site_visit = self.get_object_from_uuid(
            column='SiteVisitID',
            model=SiteVisit
        )

        chem = self.get_object_from_uuid(
            column='ChemID',
            model=Chem
        )

        if not site_visit or not chem:
            self.failed += 1
            return

        chem_value = 0.0
        chem_value_string = self.get_row_value(
            'ChemValue', return_none_if_empty=True)
        if chem_value_string:
            chem_value = float(chem_value_string)

        max_detectable_limit = 0
        max_detectable_limit_value = self.get_row_value(
            'MaxDetectableLimit',
            return_none_if_empty=True
        )
        if max_detectable_limit_value:
            max_detectable_limit = int(max_detectable_limit_value)

        (
            site_visit_chem,
            created
        ) = SiteVisitChem.objects.get_or_create(
            site_visit=site_visit,
            chem=chem,
            chem_value=chem_value,
            comment=self.get_row_value('Comment'),
            max_detectable_limit=max_detectable_limit
        )

        self.save_uuid(
            uuid=self.get_row_value('SiteVisitChemID'),
            object_id=site_visit_chem.id
        )
