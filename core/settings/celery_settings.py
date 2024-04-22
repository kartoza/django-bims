CELERY_BEAT_SCHEDULE = {
    'generate_filters': {
        'task': 'bims.tasks.generate_filters_in_all_schemas',
        'schedule': 300,
        'options': {
            'expires': 14,
            'retry': False,
            'queue': 'geocontext'
        }
    },
    # 'clean_data': {
    #     'task': 'bims.tasks.clean_data',
    #     'schedule': 30,
    #     'options': {'queue' : 'geocontext'},
    # }
}

CELERY_TIMEZONE = 'UTC'
