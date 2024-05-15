CELERY_BEAT_SCHEDULE = {
    'generate_filters': {
        'task': 'bims.tasks.generate_filters_in_all_schemas',
        'schedule': 86400,
        'options': {
            'expires': 14,
            'retry': False,
            'queue': 'geocontext'
        }
    },
}

CELERY_TIMEZONE = 'UTC'
