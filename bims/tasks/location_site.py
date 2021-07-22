# coding=utf-8
from celery import shared_task



@shared_task(name='bims.tasks.update_location_context', queue='geocontext')
def update_location_context(location_site_id, generate_site_code=False):
    from bims.utils.logger import log
    from bims.models import LocationSite
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
