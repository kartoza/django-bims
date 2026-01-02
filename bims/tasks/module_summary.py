# coding=utf-8
"""Celery task for generating module summary data."""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import connection
from django_tenants.utils import schema_context
from django.core.cache import cache

logger = get_task_logger(__name__)

LOCK_EXPIRE = 60 * 5  # Lock expires in 5 minutes


@shared_task(name='bims.tasks.generate_module_summary', queue='update')
def generate_module_summary(schema_name):
    """
    Generate and cache module summary data for the landing page.

    This task runs in the background to avoid blocking the landing page
    when the cache is empty or expired.git
    Args:
        schema_name (str): The tenant schema name
    """
    lock_id = f'module_summary_lock_{schema_name}'

    # Try to acquire lock
    acquire_lock = cache.add(lock_id, 'true', LOCK_EXPIRE)
    if not acquire_lock:
        logger.info(f'Module summary generation already in progress for schema: {schema_name}. Skipping.')
        return {
            'status': 'skipped',
            'schema': schema_name,
            'message': 'Another task is already processing this schema'
        }

    logger.info(f'Generating module summary for schema: {schema_name}')

    try:
        with schema_context(schema_name):
            from bims.api_views.module_summary import ModuleSummary
            from bims.cache import get_cache

            # Create an instance and generate the summary data
            # This will automatically cache the results
            summary_view = ModuleSummary()

            # Log cache key for debugging
            cache_key = summary_view._cache_key()
            logger.info(f'Cache key: {cache_key}')

            # Generate and cache the data
            summary_data = summary_view.summary_data()

            # Verify cache was set
            cached_result = get_cache(cache_key)
            if cached_result:
                logger.info(f'Module summary cached successfully for schema: {schema_name}')
            else:
                logger.error(f'Failed to cache module summary for schema: {schema_name}')

            logger.info(f'Module summary generated successfully for schema: {schema_name}')
            return {
                'status': 'success',
                'schema': schema_name,
                'modules_count': len(summary_data) - 1,  # Exclude general_summary
                'cached': cached_result is not None
            }
    except Exception as e:
        logger.error(f'Error generating module summary for schema {schema_name}: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        # Always release the lock
        cache.delete(lock_id)
