import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from bims.models.fbis_uuid import FbisUUID
from bims.models import LocationSite


class Command(BaseCommand):
    help = 'Migrate site owners data'

    def get_user(self, _uuid):
        ctype = ContentType.objects.get_for_model(get_user_model())
        objects = FbisUUID.objects.filter(
            uuid=_uuid,
            content_type=ctype
        )
        if objects.exists():
            return objects[0]
        return None

    def handle(self, *args, **options):
        sites_with_additional_data = LocationSite.objects.filter(
            additional_data__isnull=False,
            owner__isnull=True
        )
        index = 1
        for site in sites_with_additional_data:
            print('Processing %s/%s' % (
                index,
                sites_with_additional_data.count()
            ))
            index += 1
            additional_data = json.loads(
                site.additional_data
            )
            user = self.get_user(
                additional_data['UserID']
            )
            if user:
                print('User found %s' % user.content_object)
                site.owner = user.content_object
                site.save()
            else:
                print('User not found')
