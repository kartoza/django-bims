# coding=utf-8
"""Celery task for climate data upload"""
import csv
from celery.app import shared_task


@shared_task(name='climate.tasks.climate_upload', queue='update')
def climate_upload(session_id):
    """Background task to process climate data upload."""
    from bims.utils.logger import log
    from bims.models.upload_session import UploadSession
    from climate.scripts.climate_upload import ClimateCSVUpload

    try:
        upload_session = UploadSession.objects.get(id=session_id)
    except UploadSession.DoesNotExist:
        log('Session does not exist')
        return

    def check_header(headers):
        """Validate required headers."""
        required_headers = [
            'Station', 'Latitude', 'Longitude', 'Year', 'Month', 'Day'
        ]
        missing = [h for h in required_headers if h not in headers]
        if missing:
            error_message = (
                f'Missing required headers: {", ".join(missing)}. '
                f'Header row does not follow the correct format.'
            )
            upload_session.progress = error_message
            upload_session.error_file = upload_session.process_file
            upload_session.processed = True
            upload_session.canceled = True
            upload_session.save()
            return False
        return True

    # Read and validate headers
    csv_headers = []
    try:
        with open(upload_session.process_file.path, encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            csv_headers = reader.fieldnames
            checked = check_header(csv_headers)
    except UnicodeDecodeError:
        try:
            with open(
                upload_session.process_file.path,
                encoding='ISO-8859-1'
            ) as csv_file:
                reader = csv.DictReader(csv_file)
                csv_headers = reader.fieldnames
                checked = check_header(csv_headers)
        except Exception as e:
            upload_session.progress = f'Error reading file: {e}'
            upload_session.canceled = True
            upload_session.save()
            return
    except Exception as e:
        upload_session.progress = f'Error reading file: {e}'
        upload_session.canceled = True
        upload_session.save()
        return

    if not checked:
        return

    # Start processing
    upload_session.progress = 'Processing climate data...'
    upload_session.save()

    uploader = ClimateCSVUpload(upload_session)
    uploader.start()
