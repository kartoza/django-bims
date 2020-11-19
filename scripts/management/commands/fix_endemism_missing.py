from django.core.management import BaseCommand
from django.db.models import signals
from bims.models import *


class Command(BaseCommand):
    def handle(self, *args, **options):
        taxa_without_endemism = Taxonomy.objects.filter(
            endemism__isnull=True,
            additional_data__Endemism__isnull=False
        )
        for taxon in taxa_without_endemism:
            endemism_data = taxon.additional_data['Endemism']
            print('Updating {taxon} with {endemism}'.format(
                taxon=taxon.canonical_name,
                endemism=endemism_data
            ))
            endemism_obj, _ = Endemism.objects.get_or_create(
                name=endemism_data
            )
            taxon.endemism = endemism_obj
            taxon.save()
