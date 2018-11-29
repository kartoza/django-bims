
CELERY_BEAT_SCHEDULE = {
    'update_search_index': {
        'task': 'bims.tasks.update_search_index',
        'schedule': 18000.0,  # update every 5 hours
    },
    'update_cluster': {
        'task': 'bims.tasks.update_cluster',
        'schedule': 18000.0,  # update every 5 hours
    },
    'email_admins': {
        'task': 'bims.tasks.email_admins',
        'schedule': 604800.0,  # send email to admins every 7 days
    }
}

CELERY_TIMEZONE = 'UTC'
