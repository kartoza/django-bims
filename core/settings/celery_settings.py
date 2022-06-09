
CELERY_BEAT_SCHEDULE = {
    # 'email_admins': {
    #     'task': 'bims.tasks.email_admins',
    #     'schedule': 604800.0,  # send email to admins every 7 days
    # },
    # 'generate_spatial_scale_filter': {
    #     'task': 'bims.tasks.generate_spatial_scale_filter_if_empty',
    #     'schedule': 30,
    #     'options': {
    #     	'expires': 14,
    #     	'retry': False
    #     }
    # },
    # 'clean_data': {
    #     'task': 'bims.tasks.clean_data',
    #     'schedule': 30
    # }
}

CELERY_TIMEZONE = 'UTC'
