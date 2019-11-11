# coding=utf-8
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.mail import mail_admins
from django.template.loader import get_template
from django.utils.timezone import now
from bims.conf import TRACK_PAGEVIEWS
from bims.models import Taxonomy, BiologicalCollectionRecord, Visitor, Pageview


class Command(BaseCommand):
    help = "Script to send tracking data of BIMS site to Admins."

    def add_arguments(self, parser):
        parser.add_argument(
            '--from',
            dest='from',
            help='Start date of tracking data',
        )

        parser.add_argument(
            '--to',
            dest='to',
            help='End date of tracking data',
        )

    def handle(self, *args, **options):
        date_to = now()
        date_from = date_to - timedelta(days=7)
        if options['from']:
            date_from = options['from']

        if options['to']:
            date_to = options['to']

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
