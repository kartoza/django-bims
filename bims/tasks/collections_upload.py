# coding=utf-8
import csv
from celery import shared_task
FILE_HEADERS = [
    'UUID',
    'Latitude',
    'Longitude',
    'Sampling Date',
    'Taxon'
]

FILE_HEADERS_USER_SITE_CODE = [
    'User Site Code',
    'Original Site Code'
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

    def clean_header(header):
        return header.replace('\ufeff', '').strip()

    def check_and_clean_headers(_csv_file_path):
        with open(_csv_file_path, mode='r', newline='', encoding='utf-8') as file:
            lines = file.readlines()

            if lines:
                original_headers = lines[0].strip().split(',')
                cleaned_headers = [clean_header(header) for header in original_headers]

                cleaned_header_row = ','.join(cleaned_headers) + '\n'
                if not all(header in cleaned_headers for header in FILE_HEADERS):
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
            else:
                error_message = (
                    'File empty'
                )
                upload_session.progress = error_message
                upload_session.error_file = (
                    upload_session.process_file
                )
                upload_session.processed = True
                upload_session.save()
                return False

        with open(_csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            file.write(cleaned_header_row)
            file.writelines(lines[1:])

        return True

    checked = check_and_clean_headers(
        upload_session.process_file.path)
    if not checked:
        return

    upload_session.progress = 'Processing'
    upload_session.save()
    uploader = OccurrencesCSVUpload()
    uploader.upload_session = upload_session
    uploader.start()
