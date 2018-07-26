
CELERYBEAT_SCHEDULE = {
    'update_search_index': {
        'task': 'tasks.update_search_index',
        'schedule': 3600.0,  # update every 60 minutes
    },
    'update_cluster': {
        'task': 'tasks.update_cluster',
        'schedule': 3600.0,  # update every 60 minutes
    },
}

CELERY_TIMEZONE = 'UTC'
