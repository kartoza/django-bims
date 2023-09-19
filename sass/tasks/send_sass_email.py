# coding=utf-8
import logging
from celery import shared_task

logger = logging.getLogger('bims')


@shared_task(
    name='sass.tasks.send_sass_email', queue='update')
def send_sass_email(site_visit_id: int, user_id: int):
    from sass.models.site_visit import SiteVisit
    from django.contrib.auth import get_user_model
    from django.contrib.sites.models import Site
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    from bims.models.notification import (
        get_recipients_for_notification,
        SASS_CREATED
    )

    user = get_user_model().objects.get(id=user_id)
    site_visit = SiteVisit.objects.get(id=site_visit_id)

    ctx = {
        'collector': user,
        'owner': site_visit.owner,
        'sass_version': site_visit.sass_version,
        'site_visit_date': site_visit.site_visit_date.strftime(
            '%m/%d/%Y'),
        'site_visit_id': site_visit.id,
        'current_site': Site.objects.get_current()
    }
    email_template = 'notifications/sass_created'
    subject = render_to_string(
        '{0}_subject.txt'.format(email_template),
        ctx
    )
    email_body = render_to_string(
        '{0}_message.txt'.format(email_template),
        ctx
    )
    msg = EmailMultiAlternatives(
        subject,
        email_body,
        settings.DEFAULT_FROM_EMAIL,
        get_recipients_for_notification(
            SASS_CREATED
        )
    )
    msg.send()
