from sass.models import SassBiotopeFraction, SiteVisit, Rate
from scripts.importer.fbis_importer import FbisImporter
from bims.models import Biotope as SassBiotope


class FbisSiteVisitSassBiotopeImporter(FbisImporter):

    content_type_model = SassBiotopeFraction
    table_name = 'SiteVisitSassBiotope'
    failed = 0

    def finish_processing_rows(self):
        print('Failed : %s' % self.failed)

    def process_row(self, row, index):
        # Get rate
        rate = self.get_object_from_uuid(
            'BiotopeFraction',
            Rate)

        # Get sass biotope
        sass_biotope = self.get_object_from_uuid(
            'SassBiotopeID',
            SassBiotope)

        fraction, created = SassBiotopeFraction.objects.get_or_create(
            rate=rate,
            sass_biotope=sass_biotope,
        )

        # Get site visit
        site_visit = self.get_object_from_uuid(
            'SiteVisitID',
            SiteVisit
        )

        if not site_visit:
            self.failed += 1
            return

        if site_visit:
            if fraction not in site_visit.sass_biotope_fraction.all():
                site_visit.sass_biotope_fraction.add(fraction)
                site_visit.save()

        self.save_uuid(
            uuid=self.get_row_value('SiteVisitSassBiotopeID'),
            object_id=fraction.id
        )
