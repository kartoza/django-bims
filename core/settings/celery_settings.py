
CELERY_BEAT_SCHEDULE = {
    'email_admins': {
        'task': 'bims.tasks.email_admins',
        'schedule': 604800.0,  # send email to admins every 7 days
        'options': {'queue' : 'geocontext'},
    },
    'generate_filters': {
        'task': 'bims.tasks.generate_filters',
        'schedule': 300,
        'options': {
        	'expires': 14,
        	'retry': False,
            'queue' : 'geocontext'
        }
    },
    'clean_data': {
        'task': 'bims.tasks.clean_data',
        'schedule': 30,
        'options': {'queue' : 'geocontext'},
    }
}

CELERY_TIMEZONE = 'UTC'
