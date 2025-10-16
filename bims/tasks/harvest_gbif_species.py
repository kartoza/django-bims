# coding=utf-8
from __future__ import annotations

from celery import shared_task
from django_tenants.utils import schema_context


@shared_task(name='bims.tasks.harvest_gbif_species', queue='update')
def harvest_gbif_species(session_id, schema_name: str):
    from bims.signals.utils import disconnect_bims_signals, connect_bims_signals
    from bims.utils.logger import log
    from bims.models import HarvestSession
    from bims.utils.gbif_download import find_species_by_area

    with schema_context(schema_name):
        try:
            harvest_session = (
                HarvestSession.objects.get(id=session_id)
            )
        except HarvestSession.DoesNotExist:
            log('Session does not exist')
            return

        disconnect_bims_signals()

        if not harvest_session.status:
            harvest_session.status = 'Processing'
            harvest_session.save()

        with open(harvest_session.log_file.path, 'a') as log_file:
            log_file.write('Fetching species in area {}\n'.format(
                harvest_session.boundary.name
            ))

        parent_species = harvest_session.module_group.gbif_parent_species

        find_species_by_area(
            harvest_session.boundary_id,
            harvest_session=harvest_session,
            parent_species=parent_species,
        )

        if not HarvestSession.objects.get(id=session_id).canceled:
            harvest_session.status = 'Finished'
            harvest_session.finished = True
            harvest_session.save()

        connect_bims_signals()
