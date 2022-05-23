import csv
from celery.app import shared_task

from bims.scripts.physico_chemical_upload import PhysicoChemicalCSVUpload


@shared_task(name='bims.tasks.physico_chemical_upload', queue='update')
def physico_chemical_upload(session_id):
    from bims.utils.logger import log
    from bims.models.upload_session import UploadSession
    csv_headers = []
    try:
        upload_session = (
            UploadSession.objects.get(id=session_id)
        )
    except UploadSession.DoesNotExist:
        log('Session does not exist')
        return

    def check_header(headers):
        if 'UUID' not in headers:
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
            reader = csv.DictReader(csv_file)
            csv_headers = reader.fieldnames
            checked = check_header(csv_headers)
    except UnicodeDecodeError:
        with open(
            upload_session.process_file.path,
            encoding='ISO-8859-1'
        ) as csv_file:
            reader = csv.DictReader(csv_file)
            csv_headers = reader.fieldnames
            checked = check_header(csv_headers)

    if not checked:
        return

    upload_session.progress = 'Processing'
    upload_session.save()
    uploader = PhysicoChemicalCSVUpload()
    uploader.upload_session = upload_session
    uploader.physico_chemical_units = (
        csv_headers[csv_headers.index('Notes') + 1:]
    )
    uploader.start()
