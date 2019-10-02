# coding=utf-8
from celery import shared_task

from django.core.management import call_command



@shared_task(name='bims.tasks.update_location_context', queue='update')
def update_location_context(location_site_id):
    from bims.utils.logger import log
    from bims.models import LocationSite
    try:
        LocationSite.objects.get(id=location_site_id)
    except LocationSite.DoesNotExist:
        log('Location site does not exist')
        return

    call_command(
        'add_location_context_group',
        site_id='{}'.format(location_site_id),
        ignore_not_empty='True'
    )
