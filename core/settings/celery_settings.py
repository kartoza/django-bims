
CELERY_BEAT_SCHEDULE = {
    'update_search_index': {
        'task': 'bims.tasks.update_search_index',
        'schedule': 18000.0,  # update every 5 hours
    },
    'update_cluster': {
        'task': 'bims.tasks.update_cluster',
        'schedule': 18000.0,  # update every 5 hours
    },
}

CELERY_TIMEZONE = 'UTC'
