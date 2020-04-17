from django.core.management import BaseCommand
from bims.utils.gbif import find_species, gbif_name_suggest


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--species-name',
            dest='species_name',
            default='',
            help='Species name'
        )
        parser.add_argument(
            '-r',
            '--rank',
            dest='rank',
            default='',
            help='Rank'
        )
        parser.add_argument(
            '-k',
            '--kingdom',
            dest='kingdom',
            default='',
            help='Kingdom'
        )
        parser.add_argument(
            '-c',
            '--class',
            dest='class',
            default='',
            help='Class'
        )


    def handle(self, *args, **options):
        species = options.get('species_name', '')
        rank = options.get('rank', '')
        kingdom = options.get('kingdom', '')
        class_name = options.get('class', '')

        if not species:
            print('Need species name')

        species_data = gbif_name_suggest(q=species)

        # species_data = find_species(
        #     original_species_name=species,
        #     rank=rank,
        #     kingdom=kingdom,
        #     class_name=class_name
        # )

        print(species_data)
