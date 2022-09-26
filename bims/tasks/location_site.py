# coding=utf-8
from celery import shared_task
from bims.models import LocationSite
from bims.utils.logger import log


@shared_task(name='bims.tasks.update_location_context', queue='geocontext')
def update_location_context(location_site_id, generate_site_code=False):
    from bims.utils.location_context import get_location_context_data
    if isinstance(location_site_id, str):
        if ',' in location_site_id:
            get_location_context_data(
                site_id=str(location_site_id),
                only_empty=False,
                should_generate_site_code=generate_site_code
            )
            return
    try:
        LocationSite.objects.get(id=location_site_id)
    except LocationSite.DoesNotExist:
        log('Location site does not exist')
        return

    get_location_context_data(
        site_id=str(location_site_id),
        only_empty=False,
        should_generate_site_code=generate_site_code
    )


@shared_task(name='bims.tasks.update_site_code', queue='geocontext')
def update_site_code(location_site_id):
    from bims.models import generate_site_code

    try:
        location_site = LocationSite.objects.get(id=location_site_id)
    except LocationSite.DoesNotExist:
        log('Location site does not exist')
        return
    generate_site_code(
        location_site=location_site,
        lat=location_site.latitude,
        lon=location_site.longitude
    )
    location_site.save()
