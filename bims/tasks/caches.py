from celery import shared_task


@shared_task(
    name='bims.tasks.reset_caches',
    queue='update',
    ignore_result=True)
def reset_caches():
    from django_tenants.utils import get_tenant_model, tenant_context
    from bims.models.taxon_group import cache_taxon_groups_data, TAXON_GROUP_CACHE
    from bims.cache import get_cache

    for tenant in get_tenant_model().objects.all():
        with tenant_context(tenant):
            if not get_cache(TAXON_GROUP_CACHE):
                cache_taxon_groups_data()
