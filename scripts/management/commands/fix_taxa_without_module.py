from django.core.management import BaseCommand
from scripts.fixes.fix_taxa_without_module import (
    fix_taxa_without_modules
)

class Command(BaseCommand):
    def handle(self, *args, **options):
        fix_taxa_without_modules()
