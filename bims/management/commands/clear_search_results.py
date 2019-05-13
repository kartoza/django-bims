# coding=utf-8
"""Clear search results"""

from django.core.management.base import BaseCommand
from bims.models.search_process import SearchProcess
from bims.utils.logger import log


class Command(BaseCommand):
    """Update location site context document
    """

    def handle(self, *args, **options):
        log('Deleting all search results...')
        all_search_process = SearchProcess.objects.all()
        all_search_process.delete()
