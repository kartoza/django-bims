# coding=utf-8
from celery import shared_task



@shared_task(name='bims.tasks.update_location_context', queue='update')
def update_location_context(location_site_id):
    from bims.utils.logger import log
    from bims.models import LocationSite
    from bims.utils.location_context import get_location_context_data
    try:
        LocationSite.objects.get(id=location_site_id)
    except LocationSite.DoesNotExist:
        log('Location site does not exist')
        return

    get_location_context_data(
        site_id=str(location_site_id),
        only_empty=False
    )
