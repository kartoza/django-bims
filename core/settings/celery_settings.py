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
    'resume_harvesters': {
        'task': 'bims.tasks.auto_resume_harvest',
        'schedule': 300,
        'options': {
            'expires': 14,
            'retry': False,
            'queue': 'update'
        }
    },
}

CELERY_TIMEZONE = 'UTC'
