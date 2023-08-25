from celery import shared_task
from django.conf import settings

from bims.celery import app


@app.task(
    bind=True,
    name='geonode.tasks.notifications.send_queued_notifications',
    queue='email',
    countdown=60,
    # expires=120,
    acks_late=True,
    retry=True,
    retry_policy={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    })
def send_queued_notifications(self, *args):
    """Sends queued notifications.

    settings.PINAX_NOTIFICATIONS_QUEUE_ALL needs to be true in order to take
    advantage of this.

    """
    from importlib import import_module
    notifications = getattr(settings, 'NOTIFICATIONS_MODULE', None)

    if notifications:
        engine = import_module(f"{notifications}.engine")
        send_all = getattr(engine, 'send_all')
        # Make sure application can write to location where lock files are stored
        if not args and getattr(settings, 'NOTIFICATION_LOCK_LOCATION', None):
            send_all(settings.NOTIFICATION_LOCK_LOCATION)
        else:
            send_all(*args)


@shared_task(name='bims.tasks.send_mail_notification', queue='update')
def send_mail_notification(subject, body, from_email, recipient_list):

    from django.core.mail import send_mail
    send_mail(
        subject,
        body,
        from_email,
        recipient_list,
        fail_silently=False
    )
