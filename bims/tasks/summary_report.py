# coding=utf-8
"""Celery task for generating the general summary report."""

from celery import shared_task
from celery.utils.log import get_task_logger
from django_tenants.utils import schema_context
from django.core.cache import cache

logger = get_task_logger(__name__)

LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes


@shared_task(name='bims.tasks.generate_general_summary_report', queue='update')
def generate_general_summary_report(schema_name):
    """
    Generate and cache the general summary report.

    The report runs many aggregate queries, so it is generated in the
    background to avoid blocking the summary report page when the cache is
    empty or expired.

    Args:
        schema_name (str): The tenant schema name
    """
    lock_id = f'general_summary_report_lock_{schema_name}'

    # Try to acquire lock so only one worker generates it at a time.
    acquire_lock = cache.add(lock_id, 'true', LOCK_EXPIRE)
    if not acquire_lock:
        logger.info(
            'General summary report generation already in progress for '
            f'schema: {schema_name}. Skipping.'
        )
        return {
            'status': 'skipped',
            'schema': schema_name,
            'message': 'Another task is already processing this schema'
        }

    logger.info(f'Generating general summary report for schema: {schema_name}')

    try:
        with schema_context(schema_name):
            from bims.views.summary_report import SummaryReportGeneralApiView

            # summary_data() builds the report and stores it in the cache.
            SummaryReportGeneralApiView().summary_data()

            logger.info(
                'General summary report generated successfully for '
                f'schema: {schema_name}'
            )
            return {
                'status': 'success',
                'schema': schema_name
            }
    except Exception as e:
        logger.error(
            'Error generating general summary report for schema '
            f'{schema_name}: {str(e)}'
        )
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        # Always release the lock
        cache.delete(lock_id)
