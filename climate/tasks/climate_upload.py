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

    def clean_headers(headers):
        """Clean headers by removing BOM and extra whitespace."""
        if not headers:
            return []
        return [h.strip().lstrip('\ufeff') for h in headers]

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

    csv_headers = []
    try:
        with open(upload_session.process_file.path, encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            csv_headers = reader.fieldnames
            rows = list(reader)
    except UnicodeDecodeError:
        try:
            with open(
                upload_session.process_file.path,
                encoding='ISO-8859-1'
            ) as csv_file:
                reader = csv.DictReader(csv_file)
                csv_headers = reader.fieldnames
                rows = list(reader)
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

    cleaned_headers = clean_headers(csv_headers)
    if not check_header(cleaned_headers):
        return

    try:
        with open(
            upload_session.process_file.path, 'w',
            encoding='utf-8', newline=''
        ) as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=cleaned_headers)
            writer.writeheader()
            # Map old headers to cleaned headers for each row
            header_map = dict(zip(csv_headers, cleaned_headers))
            for row in rows:
                cleaned_row = {header_map[k]: v for k, v in row.items()}
                writer.writerow(cleaned_row)
    except Exception as e:
        upload_session.progress = f'Error rewriting file: {e}'
        upload_session.canceled = True
        upload_session.save()
        return

    # Start processing
    upload_session.progress = 'Processing climate data...'
    upload_session.save()

    uploader = ClimateCSVUpload(upload_session)
    uploader.start()
