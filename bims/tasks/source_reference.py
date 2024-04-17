# coding=utf-8
from celery import shared_task
from django.contrib.sites.models import Site
from django.core.cache import cache


def generate_source_reference_filter_by_site(site_id=None):
    if not site_id:
        all_sites = Site.objects.all()
        for site in all_sites:
            generate_source_reference_filter_by_site(
                site_id=site.id
            )
        return
    from bims.models.source_reference import (
        SourceReference
    )
    references = SourceReference.objects.filter(
        active_sites=site_id
    ).distinct('id')
    results = []
    reference_source_list = []
    for reference in references:
        if (
                reference.reference_type == 'Peer-reviewed scientific article' or
                reference.reference_type == 'Published report or thesis'
        ):
            source = u'{authors} | {year} | {title}'.format(
                authors=reference.authors,
                year=reference.year,
                title=reference.title
            )
        else:
            source = str(reference.source)
        if source not in reference_source_list:
            reference_source_list.append(source)
        else:
            continue
        results.append(
            {
                'id': reference.id,
                'reference': source,
                'type': reference.reference_type
            }
        )

    cache_key = f'source_reference_filter_{site_id}'
    cache.set(cache_key, results, timeout=None)


@shared_task(
    name='bims.tasks.generate_source_reference_filter',
    queue='update')
def generate_source_reference_filter(
        current_site_id=None):
    generate_source_reference_filter_by_site(current_site_id)


def get_source_reference_filter():
    current_site = Site.objects.get_current()
    cache_key = f'source_reference_filter_{current_site.id}'
    filter_data = cache.get(cache_key)

    if filter_data is None:
        generate_source_reference_filter(current_site.id)
        filter_data = cache.get(cache_key)

    return filter_data if filter_data else []
