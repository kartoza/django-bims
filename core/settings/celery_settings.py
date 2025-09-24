from celery.schedules import crontab

CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_MAX_LOOP_INTERVAL = 30
CELERY_BEAT_SYNC_EVERY = 1
DJANGO_CELERY_BEAT_MAX_LOOP_INTERVAL = CELERY_BEAT_MAX_LOOP_INTERVAL


CELERY_BEAT_SCHEDULE = {
    'generate_filters': {
        'task': 'bims.tasks.generate_filters_in_all_schemas',
        'schedule': 86400,
        'options': {
            'retry': False,
            'queue': 'geocontext'
        }
    },
    # 'resume_harvesters': {
    #     'task': 'bims.tasks.auto_resume_harvest_all_schemas',
    #     'schedule': 300,
    #     'options': {
    #         'retry': False,
    #         'queue': 'update'
    #     }
    # },
    # 'import-odonates-data-every-month': {
    #     'task': 'bims.tasks.import_data_task',
    #     'schedule': crontab(day_of_month='1', hour='0', minute='0'),
    #     'args': ('odonates', 100),
    #     'options': {
    #         'retry': False,
    #         'queue': 'update'
    #     }
    # },
    # 'resume-odonates-data-every-day': {
    #     'task': 'bims.tasks.import_data_task',
    #     'schedule': crontab(hour='0', minute='0'),
    #     'args': ('odonates', 100),
    #     'options': {
    #         'retry': False,
    #         'queue': 'update'
    #     }
    # },
    # 'import-anurans-data-every-month': {
    #     'task': 'bims.tasks.import_data_task',
    #     'schedule': crontab(day_of_month='1', hour='1', minute='0'),
    #     'args': ('anurans', 100),
    #     'options': {
    #         'retry': False,
    #         'queue': 'update'
    #     }
    # },
    # 'resume-anurans-data-every-day': {
    #     'task': 'bims.tasks.import_data_task',
    #     'schedule': crontab(hour='1', minute='0'),
    #     'args': ('anurans', 100),
    #     'options': {
    #         'retry': False,
    #         'queue': 'update'
    #     }
    # },
    'reset_caches': {
        'task': 'bims.tasks.reset_caches',
        'schedule': 300,
        'options': {
            'retry': False,
            'queue': 'update'
        }
    }
}
