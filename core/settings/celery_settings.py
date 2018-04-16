
CELERYBEAT_SCHEDULE = {
    'update_fish_collection_record': {
        'task': 'tasks.update_fish_collection_record',
        'schedule': 3600.0,  # update every 60 minutes
    }
}

CELERY_TIMEZONE = 'Africa/Johannesburg'
