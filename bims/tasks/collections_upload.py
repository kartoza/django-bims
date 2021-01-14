# coding=utf-8
import csv
from celery import shared_task
FILE_HEADERS = [
    'UUID',
    'Original Site Code',
    'Site description',
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
    from bims.scripts.occurrences_upload import OccurrencesCSVUpload
    try:
        upload_session = (
            TaxaUploadSession.objects.get(id=session_id)
        )
    except TaxaUploadSession.DoesNotExist:
        log('Session does not exist')
        return

    # - Check the headers
    upload_session.progress = 'Checking header row'
    upload_session.save()

    def check_header(_csv_file):
        reader = csv.DictReader(_csv_file)
        headers = reader.fieldnames
        for header in FILE_HEADERS:
            if header not in headers:
                error_message = (
                    'Header row does not follow the correct format'
                )
                upload_session.progress = error_message
                upload_session.error_file = (
                    upload_session.process_file
                )
                upload_session.processed = True
                upload_session.save()
                return False
        return True

    try:
        with open(upload_session.process_file.path) as csv_file:
            checked = check_header(csv_file)
    except UnicodeDecodeError:
        with open(
            upload_session.process_file.path,
            encoding='ISO-8859-1'
        ) as csv_file:
            checked = check_header(csv_file)

    if not checked:
        return

    upload_session.progress = 'Processing'
    upload_session.save()
    uploader = OccurrencesCSVUpload()
    uploader.upload_session = upload_session
    uploader.start()
