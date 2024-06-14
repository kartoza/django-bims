from celery import shared_task
import logging
from django.db import connection

from bims.tasks import IN_CELERY_WORKER_PROCESS

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.download_checklist', queue='update')
def download_checklist(download_request_id, send_email=False, user_id=None):
    from bims.utils.celery import memcache_lock
    from bims.api_views.checklist import generate_checklist

    def process_checklist():
        try:
            status = generate_checklist(download_request_id)
            if status:
                # send email here
                if send_email and user_id:
                    pass
            return status
        except Exception as e:
            logger.error(f"Error generating checklist for request {download_request_id}: {e}")
            raise

    def log_processing_status(download_request_id):
        logger.info(
            'Download checklist %s is already being processed by another worker',
            download_request_id
        )

    schema_name = connection.schema_name

    if IN_CELERY_WORKER_PROCESS:
        lock_id = (
            f'generate-checklist-lock-{download_request_id}-{schema_name}'
        )
        oid = f'{download_request_id} {schema_name}'

        with memcache_lock(lock_id, oid) as acquired:
            if acquired:
                return process_checklist()
            else:
                log_processing_status(download_request_id)
    else:
        return process_checklist()

    log_processing_status(download_request_id)
