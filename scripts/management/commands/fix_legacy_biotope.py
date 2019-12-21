from scripts.management.csv_command import CsvCommand
from bims.models import Biotope, BiologicalCollectionRecord


class Command(CsvCommand):

    def csv_dict_reader(self, csv_reader):
        for row in csv_reader:
            biotope_name = row['Biotope']
            biotope_objects = Biotope.objects.filter(
                name=biotope_name
            )
            if not biotope_objects.exists():
                continue
            broad_biotope_name = row['Broad Biotope']
            if broad_biotope_name == 'Stones In Current':
                broad_biotope_name += ' (SIC)'
            elif broad_biotope_name == 'Stones Out Of Current':
                broad_biotope_name += ' (SOOC)'
            broad_biotope = Biotope.objects.filter(
                name__iexact=broad_biotope_name,
                biotope_type='broad'
            )
            specific_biotope = Biotope.objects.filter(
                name__iexact=row['Specific Biotope'],
                biotope_type='specific'
            )

            substratum_name = row['Substratum']
            if substratum_name.lower() == 'sand' or substratum_name.lower() == 'silt/mud/clay':
                try:
                    sub, created = Biotope.objects.get_or_create(
                        name__iexact=substratum_name
                    )
                except Biotope.MultipleObjectsReturned:
                    biotopes = Biotope.objects.filter(
                        name__iexact=substratum_name,
                    )
                    if biotopes.filter(biotope_form__isnull=False).exists():
                        sub = biotopes.filter(biotope_form__isnull=False)[0]
                    else:
                        sub = biotopes[0]

                sub.biotope_type = 'substratum'
                sub.save()

            substratum = Biotope.objects.filter(
                name__iexact=row['Substratum'],
                biotope_type='substratum'
            )
            print('Broad : {}'.format(broad_biotope))
            print('Specific : {}'.format(specific_biotope))
            print('Substratum : {}'.format(substratum))
            collection = BiologicalCollectionRecord.objects.filter(
                biotope__in=biotope_objects
            )
            update_data = {}
            if broad_biotope.count() > 0:
                update_data['biotope'] = broad_biotope[0]
            if specific_biotope.count() > 0:
                update_data['specific_biotope'] = specific_biotope[0]
            if substratum.count() > 0:
                update_data['substratum'] = substratum[0]
            collection.update(**update_data)
            biotope_objects.delete()
