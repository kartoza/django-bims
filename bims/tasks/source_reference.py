# coding=utf-8
from celery import shared_task
from django.contrib.sites.models import Site
from django.core.cache import cache
from django_tenants.utils import tenant_context, get_tenant_model, get_tenant


def generate_source_reference_filter_by_site(tenant_id=None):
    if not tenant_id:
        for tenant in get_tenant_model().objects.all():
            with tenant_context(tenant):
                generate_source_reference_filter_by_site(tenant.id)

    tenant = get_tenant_model().objects.get(id=tenant_id)
    from bims.models.source_reference import (
        SourceReference
    )
    references = SourceReference.objects.all()
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

    cache_key = f'source_reference_filter_{tenant}'
    cache.set(cache_key, results, timeout=None)


@shared_task(
    name='bims.tasks.generate_source_reference_filter',
    queue='update')
def generate_source_reference_filter(
        tenant_id=None):
    generate_source_reference_filter_by_site(tenant_id)


def get_source_reference_filter(request):
    cache_key = f'source_reference_filter_{get_tenant(request)}'
    filter_data = cache.get(cache_key)

    if filter_data is None:
        generate_source_reference_filter(get_tenant(request).id)
        filter_data = cache.get(cache_key)

    return filter_data if filter_data else []
