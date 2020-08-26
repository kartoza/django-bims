# coding=utf-8
from celery import shared_task


@shared_task(name='bims.tasks.harvest_collections', queue='update')
def harvest_collections(session_id):
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

    harvest_session.status = 'Processing'
    harvest_session.save()

    taxonomies = harvest_session.module_group.taxonomies.all()
    index = 1

    for taxon in taxonomies:
        if HarvestSession.objects.get(id=session_id).canceled:
            print('Canceled')
            return
        harvest_session.status = 'Fetching gbif data for {c} ({i}/{t})'.format(
            c=taxon.canonical_name,
            i=index,
            t=taxonomies.count()
        )
        index += 1
        harvest_session.save()
        import_gbif_occurrences(
            taxonomy=taxon,
            log_file_path=harvest_session.log_file.path,
            session_id=session_id
        )

    harvest_session.status = 'Finished'
    harvest_session.finished = True
    harvest_session.save()
