# coding=utf-8
import csv
from celery import shared_task
FILE_HEADERS = [
    'UUID',
    'Original River Name',
    'Original Site Code',
    'Site description',
    'Refined Geomorphological Zone',
    'Latitude',
    'Longitude',
    'Sampling Date',
    'Taxon',
    'Present'
]


@shared_task(name='bims.tasks.collections_upload', queue='update')
def collections_upload(session_id):
    from bims.utils.logger import log
    from bims.models import UploadSession as TaxaUploadSession
    from bims.scripts.collections_upload import CollectionsCSVUpload
    try:
        upload_session = (
            TaxaUploadSession.objects.get(id=session_id)
        )
    except TaxaUploadSession.DoesNotExist:
        log('Session does not exist')
        return

    # - Check the headers
    upload_session.progress = 'Checking header column'
    upload_session.save()

    with open(upload_session.process_file.path) as csv_file:
        reader = csv.DictReader(csv_file)
        headers = reader.fieldnames
        for header in FILE_HEADERS:
            if header not in headers:
                error_message = (
                    'Header column is not following the correct format'
                )
                upload_session.progress = error_message
                upload_session.error_file = (
                    upload_session.process_file
                )
                upload_session.processed = True
                upload_session.save()
                return

    upload_session.progress = 'Processing'
    upload_session.save()
    taxa_csv_upload = CollectionsCSVUpload()
    taxa_csv_upload.upload_session = upload_session
    taxa_csv_upload.start()
