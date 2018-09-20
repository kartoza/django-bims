from django.core.management.base import BaseCommand
from bims.permissions.generate_permission import generate_permission
from bims.models.taxon import Taxon


class Command(BaseCommand):
    """Generate permissions for all taxon class
    """

    def handle(self, *args, **options):
        taxa = Taxon.objects.all().values('taxon_class').distinct()
        for taxon in taxa:
            generate_permission(taxon['taxon_class'])
