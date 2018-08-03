
CELERYBEAT_SCHEDULE = {
    'update_search_index': {
        'task': 'tasks.update_search_index',
        'schedule': 18000.0,  # update every 5 hours
    },
    'update_cluster': {
        'task': 'tasks.update_cluster',
        'schedule': 18000.0,  # update every 5 hours
    },
}

CELERY_TIMEZONE = 'UTC'
