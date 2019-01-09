from django.core.management.base import BaseCommand
from django.db.models import signals, Q
from bims.models.taxonomy import (
    Taxonomy,
    taxonomy_pre_save_handler,
    TaxonomicRank
)
from bims.models.vernacular_name import VernacularName
from bims.utils.gbif import get_vernacular_names


class Command(BaseCommand):
    """Update vernacular names for taxonomy.
    """

    def handle(self, *args, **options):
        taxonomies = Taxonomy.objects.filter(
            Q(rank=TaxonomicRank.SPECIES.name) |
            Q(rank=TaxonomicRank.SUBSPECIES.name)
        )
        signals.pre_save.disconnect(taxonomy_pre_save_handler)
        for taxonomy in taxonomies:
            print('Update vernacular for %s' % taxonomy.canonical_name)
            vernacular_names = get_vernacular_names(taxonomy.gbif_key)
            if 'results' not in vernacular_names:
                continue
            print('Found %s vernacular names' % len(
                vernacular_names['results']))
            for result in vernacular_names['results']:
                fields = {}
                if 'source' in result:
                    fields['source'] = result['source']
                if 'language' in result:
                    fields['language'] = result['language']
                if 'taxonKey' in result:
                    fields['taxon_key'] = int(result['taxonKey'])
                vernacular_name, status = VernacularName.objects.get_or_create(
                    name=result['vernacularName'],
                    **fields
                )
                taxonomy.vernacular_names.add(vernacular_name)
            taxonomy.save()
