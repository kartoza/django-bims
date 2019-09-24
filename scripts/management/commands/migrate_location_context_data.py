# -*- coding: utf-8 -*-
import json
from django.core.management.base import BaseCommand
from bims.models import LocationSite, LocationContext
from bims.utils.logger import log


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--location-sites',
            dest='location_sites',
            default=None,
            help='Location site'
        )

    def handle(self, *args, **options):
        site_ids = options.get('location_sites', None)
        if site_ids:
            site_ids = site_ids.split(',')

        location_sites = LocationSite.objects.filter(
            location_context__isnull=False
        )

        if site_ids:
            location_sites = location_sites.filter(id__in=site_ids)

        if not location_sites:
            log('Location site does not exist')
            return

        site_count = 1
        for site in location_sites:
            log('Migrating (%s) %s/%s' % (
                site.id, site_count, location_sites.count()))
            site_count += 1
            context_json = json.loads(site.location_context)
            try:
                for key, group in (
                        context_json['context_group_values'].iteritems()):
                    group_key = group['key']
                    if isinstance(group['service_registry_values'], list):
                        continue
                    for k, context_value in (
                            group['service_registry_values'].iteritems()):
                        context_key = context_value['key']
                        context_name = context_value['name']
                        context_value = str(context_value['value'])
                        LocationContext.objects.get_or_create(
                            site=site,
                            group_key=group_key,
                            key=context_key,
                            name=context_name,
                            value=context_value
                        )
            except (KeyError, UnicodeEncodeError):
                continue
            site.location_context = None
            site.location_context_document = None
            site.save()
