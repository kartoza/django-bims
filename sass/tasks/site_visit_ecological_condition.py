# coding=utf-8
import logging
from celery import shared_task

logger = logging.getLogger('bims')


@shared_task(
    name='sass.tasks.site_visit_ecological_condition_task', queue='update')
def site_visit_ecological_condition_task(site_visit_id: int):
    from sass.models.site_visit import SiteVisit
    from sass.scripts.site_visit_ecological_condition_generator import (
        generate_site_visit_ecological_condition
    )
    site_visit = SiteVisit.objects.get(id=site_visit_id)
    logger.info(
        f'Generating ecological condition for site visit {site_visit.id}')
    generate_site_visit_ecological_condition([site_visit])
