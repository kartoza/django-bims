import re
from scripts.management.csv_command import CsvCommand
from bims.models import BiologicalCollectionRecord, Taxonomy
from django.db.models import F, Q


class Command(CsvCommand):
    """
    This script aims to fix the different name of original species name
    from BiologicalCollectionRecord object with species name from Taxonomy
    object.
    """

    def handle(self, *args, **options):
        bio = BiologicalCollectionRecord.objects.exclude(
            Q(taxonomy__canonical_name__icontains=F('original_species_name')) |
            Q(taxonomy__legacy_canonical_name__icontains=F('original_species_name'))
        )
        unique_canonical_names = bio.distinct(
            'original_species_name').values_list(
            'original_species_name', flat=True
        )
        for original_species_name in unique_canonical_names:
            original_species_name = original_species_name.strip()
            taxa = Taxonomy.objects.filter(
                Q(canonical_name__iexact=original_species_name) |
                Q(legacy_canonical_name__icontains=original_species_name)
            )
            if not taxa.exists():
                # Check if original species name has weird character
                if bool(re.search(r'\d|sp.|\(|\)', original_species_name)):
                    canonical_name = original_species_name.split(' ')[0]
                    taxa = Taxonomy.objects.filter(
                        Q(canonical_name__iexact=canonical_name) |
                        Q(legacy_canonical_name__icontains=canonical_name)
                    )

            if taxa.exists():
                print(
                    '--- Updating taxon object of {species} to {taxon} ---'
                        .format(
                            species=original_species_name,
                            taxon=str(taxa[0])))
                bio.filter(
                    original_species_name=original_species_name
                ).update(
                    taxonomy=taxa[0]
                )
