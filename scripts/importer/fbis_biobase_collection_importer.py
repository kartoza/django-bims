from datetime import datetime
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from scripts.importer.fbis_postgres_importer import FbisPostgresImporter
from easyaudit.signals.model_signals import pre_save as easyaudit_presave
from geonode.people.models import Profile
from bims.models import (
    BiologicalCollectionRecord, LocationSite,
    Biotope, SourceReferenceBibliography,
    FbisUUID,
    collection_post_save_handler
)
from bims.utils.gbif import search_taxon_identifier


class FbisBiobaseCollectionImporter(FbisPostgresImporter):

    table_name = '"BiobaseCollectionRecord"'
    content_type_model = BiologicalCollectionRecord
    species_ranks = [
        'GenusSpecies',
        'SubFamily',
        'Family',
        'SubOrder',
        'Order',
        'Class',
        'Phylum',
    ]

    def start_processing_rows(self):
        signals.post_save.disconnect(
            collection_post_save_handler,
        )
        signals.pre_save.disconnect(
            easyaudit_presave,
            dispatch_uid='easy_audit_signals_pre_save'
        )

    def finish_processing_rows(self):
        signals.post_save.connect(
            collection_post_save_handler,
        )

    def process_row(self, row, index):
        current_species_rank = 0
        original_species_name = self.get_row_value(
            'OriginalSpeciesName'
        )
        abundance = self.get_row_value(
            'Abundance'
        )
        if abundance:
            abundance = float(abundance)
        else:
            abundance = None
        present = self.get_row_value(
            'Present'
        )
        biotope = self.get_object_from_uuid(
            column='BioBiotopeID',
            model=Biotope
        )
        site = self.get_object_from_uuid(
            column='BioSiteID',
            model=LocationSite
        )
        source_reference = self.get_object_from_uuid(
            column='BioReferenceID',
            model=SourceReferenceBibliography
        )
        month = self.get_row_value(
            'Month'
        )
        if month == 13:
            month = 1
        year = self.get_row_value(
            'Year'
        )
        date_string = '{year}-{month}-{day}'.format(
            day=1,
            month=month,
            year=year
        )

        # Get taxonomy detail
        taxonomy_unspecified = False
        species = self.get_row_value(
            self.species_ranks[current_species_rank]
        )
        while (
                species.lower() == 'unspecified' and
                current_species_rank < len(self.species_ranks) and
                not taxonomy_unspecified
        ):
            current_species_rank += 1
            try:
                species = self.get_row_value(
                    self.species_ranks[current_species_rank]
                )
            except IndexError:
                taxonomy_unspecified = True

        if not taxonomy_unspecified:
            taxonomy = search_taxon_identifier(species)
            while (
                    not taxonomy and
                    current_species_rank < len(self.species_ranks) and
                    not taxonomy_unspecified
            ):
                current_species_rank += 1
                try:
                    species = self.get_row_value(
                        self.species_ranks[current_species_rank]
                    )
                    taxonomy = search_taxon_identifier(species)
                except IndexError:
                    taxonomy = None
                    taxonomy_unspecified = True
        else:
            taxonomy = None

        collection, created = BiologicalCollectionRecord.objects.get_or_create(
            original_species_name=original_species_name,
            taxonomy=taxonomy,
            site=site,
            biotope=biotope,
            present=present == 1,
            abundance_number=abundance,
            collection_date=datetime.strptime(date_string, '%Y-%m-%d'),
            validated=True
        )

        collection.additional_data = {
            'BioBaseData': True,
            'BioDate': self.get_row_value('BioDate'),
            'Season': self.get_row_value('Season'),
            'WarningType': self.get_row_value('WarningType'),
            'WarningDescription': self.get_row_value('WarningDescription'),
            'User': self.get_row_value('User')
        }

        collection.source_reference = source_reference

        user_ctype = ContentType.objects.get_for_model(
            Profile
        )
        owners = FbisUUID.objects.filter(
            uuid=self.get_row_value('User'),
            content_type=user_ctype
        )
        if owners.exists():
            collection.owner = owners[0]
            collection.collector_user = owners[0]
        else:
            superusers = get_user_model().objects.filter(is_superuser=True)
            if superusers.exists():
                collection.owner = superusers[0]
                collection.collector_user = superusers[0]

        collection.save()

        self.save_uuid(
            uuid=self.get_row_value('BioSiteVisitBioBiotopeTaxonID'),
            object_id=biotope.id
        )
