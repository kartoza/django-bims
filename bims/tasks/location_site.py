# coding=utf-8
import logging

from django.db.models import signals, OuterRef, Exists

from celery import shared_task

from bims.cache import set_cache, HARVESTING_GEOCONTEXT
from bims.utils.logger import log

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.location_sites_overview', queue='search')
def location_sites_overview(
        search_parameters=None,
        search_process_id=None
):
    from bims.utils.celery import memcache_lock
    from bims.api_views.location_site_overview import (
        LocationSiteOverviewData
    )
    from bims.models.search_process import (
        SearchProcess,
        SEARCH_PROCESSING,
        SEARCH_FINISHED
    )

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(
            id=search_process_id
        )
    except SearchProcess.DoesNotExist:
        return

    lock_id = '{0}-lock-{1}'.format(
        search_process.file_path,
        search_process.process_id
    )
    oid = '{0}'.format(search_process.process_id)
    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            search_process.set_status(SEARCH_PROCESSING)

            overview_data = LocationSiteOverviewData()
            if search_process.requester and 'requester' not in search_parameters:
                search_parameters['requester'] = search_process.requester.id

            overview_data.search_filters = search_parameters

            results = dict()
            results[LocationSiteOverviewData.BIODIVERSITY_DATA] = (
                overview_data.biodiversity_data()
            )
            results[LocationSiteOverviewData.SASS_EXIST] = (
                overview_data.is_sass_exist
            )
            search_process.set_status(SEARCH_FINISHED, False)
            search_process.save_to_file(results)
    logger.info(
        'Search %s is already being processed by another worker',
        search_process.process_id)


@shared_task(bind=True, name='bims.tasks.update_location_context', queue='geocontext')
def update_location_context(
        self,
        location_site_id,
        generate_site_code=False,
        generate_filter=True,
        only_empty=False):
    from bims.models import LocationSite, location_site_post_save_handler
    from bims.utils.location_context import get_location_context_data
    from bims.models.location_context_group import LocationContextGroup
    from bims.models.location_context_filter_group_order import (
        location_context_post_save_handler
    )
    group_keys = None

    self.update_state(state='STARTED', meta={'process': 'Checking location site'})

    if not location_site_id:
        self.update_state(
            state='PROGRESS',
            meta={'process': 'Updating location context for multiple sites'})
        try:
            get_location_context_data(
                group_keys=group_keys,
                site_id=None,
                only_empty=only_empty,
                should_generate_site_code=generate_site_code
            )
        except Exception:
            set_cache(HARVESTING_GEOCONTEXT, False)
        return

    if isinstance(location_site_id, str):
        self.update_state(
            state='PROGRESS',
            meta={'process': 'Updating location context for multiple IDs'})
        if ',' in location_site_id:
            get_location_context_data(
                group_keys=group_keys,
                site_id=str(location_site_id),
                only_empty=only_empty,
                should_generate_site_code=generate_site_code
            )
            return
    try:
        LocationSite.objects.get(id=location_site_id)
    except LocationSite.DoesNotExist:
        log('Location site does not exist')
        return

    if not generate_filter:
        signals.post_save.disconnect(
            location_context_post_save_handler,
            sender=LocationContextGroup
        )
    signals.post_save.disconnect(
        location_site_post_save_handler,
        sender=LocationSite
    )
    self.update_state(state='PROGRESS', meta={'process': 'Updating location context'})
    get_location_context_data(
        group_keys=group_keys,
        site_id=str(location_site_id),
        only_empty=False,
        should_generate_site_code=generate_site_code
    )
    self.update_state(state='SUCCESS')
    signals.post_save.connect(
        location_site_post_save_handler,
        sender=LocationSite
    )
    if not generate_filter:
        signals.post_save.connect(
            location_context_post_save_handler,
            sender=LocationContextGroup
        )
    return 'Finished updating location context'


@shared_task(name='bims.tasks.update_site_code', queue='geocontext')
def update_site_code(location_site_ids):
    from bims.models import LocationSite
    from bims.models import generate_site_code

    for location_site_id in location_site_ids:
        try:
            location_site = LocationSite.objects.get(id=location_site_id)
        except LocationSite.DoesNotExist:
            continue
        location_site.site_code, catchments_data = generate_site_code(
            location_site=location_site,
            lat=location_site.latitude,
            lon=location_site.longitude
        )
        location_site.save()


@shared_task(name='bims.tasks.remove_dangling_sites', queue='geocontext')
def remove_dangling_sites():
    from bims.models.location_site import LocationSite
    from bims.models.location_context import LocationContext

    qs = LocationSite.objects.all()

    for rel in LocationSite._meta.get_fields():
        if not (rel.auto_created and not rel.concrete):
            continue  # skip normal fields

        # ── skip LocationContext completely
        if rel.related_model is LocationContext:
            continue

        related_model = rel.related_model
        link_field = (
            rel.field.name
            if hasattr(rel, "field") and rel.field
            else rel.field.m2m_field_name()
        )
        sub = related_model.objects.filter(**{link_field: OuterRef("pk")})
        qs = qs.filter(~Exists(sub))

    total = qs.count()
    deleted, _ = qs.delete()
    log(f"Deleted {deleted}/{total} dangling LocationSite rows.")
