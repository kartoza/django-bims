
CELERY_BEAT_SCHEDULE = {
    'email_admins': {
        'task': 'bims.tasks.email_admins',
        'schedule': 604800.0,  # send email to admins every 7 days
    }
}

CELERY_TIMEZONE = 'UTC'
