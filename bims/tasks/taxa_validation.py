# coding=utf-8
"""Celery task for taxa validation."""
from celery import shared_task


@shared_task(name='bims.tasks.taxa_validation', queue='update')
def taxa_validation_task(session_id):
    """
    Async task for validating taxa CSV files.

    Generates a validated CSV with _validation_status column.
    """
    from bims.utils.logger import log
    from bims.models import UploadSession
    from bims.scripts.taxa_validation import TaxaValidator

    try:
        upload_session = UploadSession.objects.get(id=session_id)
    except UploadSession.DoesNotExist:
        log('Validation session does not exist')
        return

    upload_session.progress = 'Starting validation...'
    upload_session.save()

    validator = TaxaValidator(upload_session)
    validator.validate_file()
