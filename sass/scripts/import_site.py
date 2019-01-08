import os
from django.conf import settings
from django.db.models import signals
from bims.models import (
    FbisUUID,
    LocationSite,
    location_site_post_save_handler
)


def import_site_table(accdb_file_name):
    accdb_filepath = os.path.join(
        settings.MEDIA_ROOT,
        accdb_file_name
    )
    if not os.path.isfile(accdb_filepath):
        print('%s not found in media directory' % accdb_file_name)
        return
    signals.post_save.disconnect(
        location_site_post_save_handler,
    )

    sites = LocationSite.objects.all()[:3]
    for site in sites:
        site.save()

    signals.post_save.connect(
        location_site_post_save_handler
    )
