from django.db.models import F, CharField, Count
from django.db.models.functions import Concat
from django.core.management import BaseCommand
from bims.models import BiologicalCollectionRecord


class Command(BaseCommand):
    # Update location sites to use
    # legacy site codes if they have correct format

    def handle(self, *args, **options):
        qs = BiologicalCollectionRecord.objects.annotate(
            dupe_id=Concat(F('additional_data'), F('collection_date'),
                           F('taxonomy_id'), F('site_id'), F('abundance_number'), F('source_reference_id'),
                           output_field=CharField()))

        dupes = qs.values('dupe_id', 'collection_date', 'taxonomy_id', 'site_id', 'abundance_number', 'source_reference_id', 'additional_data').annotate(
            dupe_count=Count('dupe_id')).filter(
            dupe_count__gt=1)

        errors = []
        index = 0

        for dupe in dupes:
            index += 1
            print('Processing {i}/{j}'.format(i=index, j=dupes.count()))
            try:
                # qs.filter(dupe_id=dupe['dupe_id'])
                collections = BiologicalCollectionRecord.objects.filter(
                    collection_date=dupe['collection_date'],
                    taxonomy_id=dupe['taxonomy_id'],
                    site_id=dupe['site_id'],
                    abundance_number=dupe['abundance_number'],
                    source_reference_id=dupe['source_reference_id'])

                if collections.exclude(owner__isnull=True).count() == 0:
                    print('No collections owner found, '
                        'set to admin for first collection, delete the rest')
                    collection_to_keep = collections[0]
                    collection_to_keep.owner_id = 157
                    collection_to_keep.save()
                    collections.exclude(id=collection_to_keep.id).delete()
                    continue
                if collections.exclude(owner_id=157).exists():
                    print('Found collection(s) with owner not admin, delete the rest')
                    collection_to_keep = collections.exclude(owner_id=157)[0]
                    collections.exclude(id=collection_to_keep.id).delete()
                    continue
                print('All collections are owned by admin')
                collection_to_keep = collections[0]
                collections.exclude(id=collection_to_keep.id).delete()
            except Exception as e:
                errors.append('{index}/{error}'.format(
                    index=index,
                    error=str(e)
                ))
