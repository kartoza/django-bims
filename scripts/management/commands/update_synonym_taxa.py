from bims.models.taxonomy import Taxonomy
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Update taxa with synonym status.
    """

    def handle(self, *args, **options):
        index = 0
        taxa = Taxonomy.objects.filter(
            taxonomic_status='SYNONYM',
            accepted_taxonomy__isnull=True
        ).exclude(gbif_key__isnull=True)
        total_taxa = taxa.count()
        for taxon in taxa:
            if taxon.additional_data:
                taxon.additional_data['fetch_gbif'] = True
            else:
                taxon.additional_data = {'fetch_gbif': True}
            taxon.save()
            print(f'Updating {index}/{total_taxa.count}')
            index += 1
