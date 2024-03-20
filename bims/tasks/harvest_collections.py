# coding=utf-8
from celery import shared_task
import re


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
            site_id=harvest_session.source_site_id,
            offset=offset,
            area_index=area_index
        )
        offset = 0
        area_index = 1

    harvest_session.status = 'Finished'
    harvest_session.finished = True
    harvest_session.save()

    connect_bims_signals()
