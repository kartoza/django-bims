# coding=utf-8
import os

from celery import shared_task
import re
import logging

from django.db.models import Max, Subquery, OuterRef

from bims.cache import get_cache, set_cache, delete_cache

logger = logging.getLogger(__name__)


def find_last_index(pattern_str, filepath) -> int:
    # Pattern to match the URL and extract the offset
    pattern = re.compile(pattern_str)

    # Open the file
    with open(filepath, 'rb') as f:
        # Go to the end of the file
        f.seek(0, 2)
        # Get the current position, which is the size of the file
        filesize = f.tell()

        # Starting from the end, read backwards
        linesize = 1024
        for i in range(filesize // linesize + 1):
            # Calculate the start of the next block to read
            start = max(0, filesize - (i + 1) * linesize)
            # Calculate the size of the block to read
            size = min(linesize, filesize - start)

            # Go to the start of the next block
            f.seek(start)
            # Read the block
            block = f.read(size).decode('utf-8', errors='ignore')

            # Since we're reading backwards, reverse the block and search for the pattern
            for line in reversed(block.splitlines()):
                match = pattern.search(line)
                if match:
                    return int(match.group(1))

    return 0


@shared_task(name='bims.tasks.harvest_collections', queue='update')
def harvest_collections(session_id, resume=False):
    from bims.signals.utils import disconnect_bims_signals, connect_bims_signals
    from bims.utils.logger import log
    from bims.models import HarvestSession
    from django.db.models import Q
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

    disconnect_bims_signals()

    taxonomies = harvest_session.module_group.taxonomies.filter(
        Q(rank='GENUS') | Q(rank='SPECIES') | Q(rank='SUBSPECIES')
    )
    index = 1
    offset = 0
    area_index = 1

    if resume and harvest_session.status:
        match = re.search(r'\((\d+)/', harvest_session.status)
        # Extract the number if found
        index = int(match.group(1)) if match else 1
        offset = find_last_index(
            r'&offset=(\d+)',
            harvest_session.log_file.path
        )
        area_index = find_last_index(
            r'Area=\((\d+)/(\d+)\)',
            harvest_session.log_file.path
        )
        if area_index == 0:
            area_index = 1

    if resume and harvest_session.canceled:
        harvest_session.canceled = False
        harvest_session.save()

    taxonomies_start_index = index - 1

    for taxon in taxonomies[taxonomies_start_index:]:
        if HarvestSession.objects.get(id=session_id).canceled:
            print('Canceled')
            connect_bims_signals()
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
            session_id=session_id,
            taxon_group=harvest_session.module_group,
            offset=offset,
            area_index=area_index
        )
        offset = 0
        area_index = 1

    harvest_session.status = 'Finished'
    harvest_session.finished = True
    harvest_session.save()

    connect_bims_signals()


@shared_task(
    name='bims.tasks.auto_resume_harvest',
    queue='update',
    ignore_result=True)
def auto_resume_harvest():
    from bims.models.harvest_session import HarvestSession
    try:
        # Subquery to get the latest harvest session id for each harvester
        latest_sessions_subquery = HarvestSession.objects.filter(
            harvester=OuterRef('harvester'),
            finished=False,
            canceled=False
        ).order_by('-id').values('id')[:1]

        # Retrieve the latest harvest session for each harvester that meets the conditions
        harvest_sessions = HarvestSession.objects.filter(
            id__in=Subquery(latest_sessions_subquery)
        )

        harvester_keys_label = 'harvester_keys'
        new_harvester_keys = []

        for session in harvest_sessions:
            cache_key = f'harvester_{session.id}_last_log'
            last_log_line = read_last_line(session.log_file)

            # Retrieve the last known log line from the cache
            cached_log_line = get_cache(cache_key)
            new_harvester_keys.append(session.id)

            # Compare log lines to determine if the session needs to be resumed
            if cached_log_line and last_log_line == cached_log_line:
                logger.info(f"Resuming harvest session for harvester {session.harvester_id}.")
                harvest_collections.delay(session.id, True)

            # Update the cache with the current last log line
            set_cache(cache_key, last_log_line)

        # Remove old caches for harvesters that are no longer active
        old_harvester_keys = get_cache(harvester_keys_label, [])
        for old_key in old_harvester_keys:
            if old_key not in new_harvester_keys:
                delete_cache(f'harvester_{old_key}_last_log')

        # Update the cache with the current active harvester keys
        set_cache(harvester_keys_label, new_harvester_keys)

    except Exception as e:
        logger.error(f"Error in auto_resume_harvest: {str(e)}")


import os
import logging

logger = logging.getLogger(__name__)


def read_last_line(log_file):
    """Read the last non-empty line of the log file."""
    try:
        if log_file and log_file.path:
            with open(log_file.path, 'rb') as f:
                f.seek(-1, os.SEEK_END)

                # Handle case where file is empty or has only newlines
                if f.read(1) == b'\n':
                    f.seek(-2, os.SEEK_END)

                # Read backwards until we find a non-empty line
                while f.tell() > 0:
                    f.seek(-2, os.SEEK_CUR)
                    while f.read(1) != b'\n' and f.tell() > 1:
                        f.seek(-2, os.SEEK_CUR)

                    last_line = f.readline().decode().strip()

                    if last_line:  # Return if the line is not empty
                        return last_line

                    f.seek(-2, os.SEEK_CUR)  # Move back before the current line

                # If reached the beginning of the file
                f.seek(0)
                first_line = f.readline().decode().strip()
                return first_line if first_line else ''
        return ''
    except Exception as e:
        logger.error(f"Error reading last line of log file: {str(e)}")
        return ''

@shared_task(
    name='bims.tasks.auto_resume_harvest_all_schemas',
    queue='update',
    ignore_result=True
)
def auto_resume_harvest_all_schemas():
    from django_tenants.utils import get_tenant_model, tenant_context

    for tenant in get_tenant_model().objects.all():
        with tenant_context(tenant):
            auto_resume_harvest()
