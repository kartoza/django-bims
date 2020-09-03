from django.db.models import F, CharField, Count
from django.db.models.functions import Concat
from django.core.management import BaseCommand
from bims.models import BiologicalCollectionRecord


class Command(BaseCommand):
    """
    Remove duplicated biological collection records
    """

    def handle(self, *args, **options):
        qs = BiologicalCollectionRecord.objects.filter(survey__isnull=True).annotate(
            dupe_id=Concat(F('collection_date'), F('site_id'), F('collector_user_id'), F('owner_id'),
                           output_field=CharField()))

        dupes = qs.values('dupe_id', 'collection_date', 'site_id', 'collector_user_id', 'owner_id').annotate(
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
                    site_id=dupe['site_id'],
                    owner_id=dupe['owner_id'],
                    collector_user_id=dupe['collector_user_id'])

                try:
                    survey, _ = Survey.objects.get_or_create(
                        site_id=dupe['site_id'],
                        date=dupe['collection_date'],
                        collector_user_id=dupe['collector_user_id'],
                        owner_id=dupe['owner_id']
                    )
                except Survey.MultipleObjectsReturned:
                    survey = Survey.objects.get_or_create(
                        site_id=dupe['site_id'],
                        date=dupe['collection_date'],
                        collector_user_id=dupe['collector_user_id'],
                        owner_id=dupe['owner_id']
                    )[0]

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
