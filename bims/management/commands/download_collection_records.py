# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from bims.tasks.collection_record import download_collection_record_task


class Command(BaseCommand):

    def handle(self, *args, **options):
        request = {'taxon': [""], 'search': ["Galaxias zebratus"],
                   'siteId': [""], 'collector': [""], 'category': [""],
                   'yearFrom': [""], 'yearTo': [""], 'months': [""],
                   'boundary': [""], 'userBoundary': [""],
                   'referenceCategory': [""], 'spatialFilter': [""],
                   'reference': [""], 'endemic': [""],
                   'conservationStatus': ["[]"], 'modules': ["1"],
                   'validated': [""],
                   'sourceCollection': ['["fbis", "gbif"]'],
                   'abioticData': [""], 'ecologicalCategory': [""],
                   'rank': [""], 'siteIdOpen': [""], 'orderBy': ["name"],
                   'polygon': [""], 'thermalModule': [""], 'dst': [""],
                   'downloadRequestId': ''}
        path_file = (
            '/home/web/media/processed_csv/download_csv_test.csv'
        )
        send_email = False
        download_collection_record_task(
            request=request,
            path_file=path_file,
            send_email=send_email
        )
