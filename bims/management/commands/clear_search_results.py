# coding=utf-8
"""Clear search results"""
from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, tenant_context

from bims.models.search_process import SearchProcess
from bims.utils.logger import log


class Command(BaseCommand):
    """Update location site context document
    """

    def handle(self, *args, **options):
        log('Deleting all search results...')

        for tenant in get_tenant_model().objects.exclude(schema_name='public'):
            with tenant_context(tenant):
                all_search_process = SearchProcess.objects.all()
                all_search_process.delete()
