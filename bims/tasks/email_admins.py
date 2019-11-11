# coding=utf-8
from celery import shared_task


@shared_task(name='bims.tasks.email_admins', queue='update')
def email_admins():
    from datetime import timedelta
    from django.core.mail import mail_admins
    from django.template.loader import get_template
    from django.utils.timezone import now
    from bims.conf import TRACK_PAGEVIEWS
    from bims.models import (
        BiologicalCollectionRecord, Visitor, Pageview, Taxonomy
    )

    date_to = now()
    date_from = date_to - timedelta(days=7)

    taxon_count = Taxonomy.objects.count()
    collections_count = \
        BiologicalCollectionRecord.objects.filter(validated=True).count()

    html = get_template('tracking/email.html')
    user_stats = Visitor.objects.user_stats(date_from, date_to)
    visitor_stats = Visitor.objects.stats(date_from, date_to)
    if TRACK_PAGEVIEWS:
        pageview_stats = Pageview.objects.stats(date_from, date_to)
    else:
        pageview_stats = None
    context = {
        'user_stats': user_stats,
        'visitor_stats': visitor_stats,
        'pageview_stats': pageview_stats,
        'taxon_count': taxon_count,
        'collections_count': collections_count,
        'date_from': date_from,
        'date_to': date_to
    }

    html_content = html.render(context)

    mail_admins(
        'BIMS site activity report',
        'Dear Admin\n'
        'The following data is the activity report of the BIMS site '
        'from {} to {}:\n'
        'Current taxon count: {}\n'
        'Current collections count: {}\n'
        'Kind regards,\n'
        'BIMS'.format(date_from, date_to, taxon_count, collections_count),
        html_message=html_content
    )
