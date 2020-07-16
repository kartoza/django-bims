# coding=utf-8
import csv
from celery import shared_task


@shared_task(name='bims.tasks.harvest_collections', queue='update')
def harvest_collections(session_id):
    import os
    from django.core.files import File
    from django.conf import settings
    from bims.utils.logger import log
    from bims.models import HarvestSession
    from bims.scripts.import_gbif_occurrences import (
        import_gbif_occurrences
    )
    try:
        harvest_session = (
            HarvestSession.objects.get(id=session_id)
        )
    except HarvestSession.DoesNotExist:
        log('Session does not exist')
        return

    # - Check the headers
    harvest_session.progress = 'Checking header row'
    harvest_session.save()

    log_file_folder = os.path.join(
        settings.MEDIA_ROOT, 'harvest-session-log'
    )

    log_file_path = os.path.join(
        log_file_folder, '{id}-{time}.txt'.format(
            id=session_id,
            time=harvest_session.start_time.strftime("%s")
        )
    )

    if not os.path.exists(log_file_folder):
        os.mkdir(log_file_folder)

    with open(log_file_path, 'a+') as fi:
        harvest_session.log_file = File(fi, name=os.path.basename(fi.name))
        harvest_session.save()

    harvest_session.progress = 'Processing'
    harvest_session.save()

