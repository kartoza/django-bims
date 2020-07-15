# coding=utf-8
import csv
from celery import shared_task
from bims.scripts.species_keys import *  # noqa
TAXA_FILE_HEADERS = [
    TAXON_RANK,
    TAXON,
    SCIENTIFIC_NAME,
    ORIGIN,
    ENDEMISM,
    CONSERVATION_STATUS
]


@shared_task(name='bims.tasks.taxa_upload', queue='update')
def taxa_upload(taxa_upload_session_id):
    from bims.utils.logger import log
    from bims.models import UploadSession as TaxaUploadSession
    from bims.scripts.taxa_upload import TaxaCSVUpload
    try:
        taxa_upload_session = (
            TaxaUploadSession.objects.get(id=taxa_upload_session_id)
        )
    except TaxaUploadSession.DoesNotExist:
        log('Taxa session does not exist')
        return

    # - Check the headers
    taxa_upload_session.progress = 'Checking header row'
    taxa_upload_session.save()

    with open(taxa_upload_session.process_file.path) as csv_file:
        reader = csv.DictReader(csv_file)
        headers = reader.fieldnames
        for header in TAXA_FILE_HEADERS:
            if header not in headers:
                error_message = (
                    'Header row is not following the correct format'
                )
                taxa_upload_session.progress = error_message
                taxa_upload_session.error_file = (
                    taxa_upload_session.process_file
                )
                taxa_upload_session.processed = True
                taxa_upload_session.save()
                return

    taxa_upload_session.progress = 'Processing'
    taxa_upload_session.save()
    taxa_csv_upload = TaxaCSVUpload()
    taxa_csv_upload.upload_session = taxa_upload_session
    taxa_csv_upload.start()
