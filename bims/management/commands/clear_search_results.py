# coding=utf-8
"""Clear search results"""
import os
import shutil
from django.conf import settings
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
        csv_path = os.path.join(
            settings.MEDIA_ROOT,
            'csv_processed'
        )
        shutil.rmtree(csv_path)
        os.mkdir(csv_path)
