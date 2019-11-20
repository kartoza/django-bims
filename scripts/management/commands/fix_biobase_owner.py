from django.core.management import BaseCommand
from django.db.models import signals
from bims.models import (
    BiologicalCollectionRecord,
    location_site_post_save_handler,
    collection_post_save_handler
)
from bims.utils.logger import log


class Command(BaseCommand):
    def handle(self, *args, **options):
        signals.post_save.disconnect(
            location_site_post_save_handler
        )
        signals.post_save.disconnect(
            collection_post_save_handler
        )

        biobase_collection = BiologicalCollectionRecord.objects.filter(
            additional_data__BioBaseData=True
        )
        index = 0
        for biobase in biobase_collection:
            index += 1
            print('Processing -- %s/%s' % (index, biobase_collection.count()))
            if not biobase.source_reference:
                continue
            authors = biobase.source_reference.source.get_authors()
            try:
                author = authors[0]
                if not author.user:
                    author.save()
                author_user = (
                    biobase.source_reference.source.get_authors()[0].user
                )
                if biobase.owner != author_user:
                    biobase.owner = author_user
                    biobase.save()
                    log('Collection {id} - new owner : {owner}'.format(
                        id=biobase.id,
                        owner=biobase.owner
                    ))
                if biobase.site.owner != author_user:
                    biobase.site.owner = author_user
                    biobase.site.save()
                    log('Site {id} - new owner : {owner}'.format(
                        id=biobase.site.id,
                        owner=biobase.site.owner
                    ))
            except IndexError:
                continue
