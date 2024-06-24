from celery.schedules import crontab


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
        'task': 'bims.tasks.auto_resume_harvest_all_schemas',
        'schedule': 300,
        'options': {
            'expires': 14,
            'retry': False,
            'queue': 'update'
        }
    },'import-odonates-data-every-month': {
        'task': 'bims.tasks.import_data_task',
        'schedule': crontab(day_of_month='1', hour='0', minute='0'),
        'args': ('odonates', 100)
    },
    'resume-odonates-data-every-day': {
        'task': 'bims.tasks.import_data_task',
        'schedule': crontab(hour='0', minute='0'),
        'args': ('odonates', 100)
    },
    'import-anurans-data-every-month': {
        'task': 'bims..tasks.import_data_task',
        'schedule': crontab(day_of_month='1', hour='1', minute='0'),
        'args': ('anurans', 100)
    },
    'resume-anurans-data-every-day': {
        'task': 'bims..tasks.import_data_task',
        'schedule': crontab(hour='1', minute='0'),
        'args': ('anurans', 100)
    },
}

CELERY_TIMEZONE = 'UTC'
