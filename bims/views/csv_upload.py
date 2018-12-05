# coding=utf-8
"""CSV uploader view
"""

import csv
import sys
from datetime import datetime
from django.urls import reverse_lazy
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.views.generic import FormView
from django.http import JsonResponse
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from bims.forms.csv_upload import CsvUploadForm
from bims.models import (
    LocationSite,
    LocationType,
)
from bims.models.location_site import (
    location_site_post_save_handler
)
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord,
    collection_post_save_update_cluster
)
from bims.utils.gbif import update_collection_record


class CsvUploadView(UserPassesTestMixin, LoginRequiredMixin, FormView):
    """Csv upload view."""

    form_class = CsvUploadForm
    template_name = 'csv_uploader.html'
    context_data = dict()
    success_url = reverse_lazy('csv-upload')
    collection_record = BiologicalCollectionRecord

    def test_func(self):
        return self.request.user.has_perm('bims.can_upload_csv')

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to upload CSV')
        return super(CsvUploadView, self).handle_no_permission()

    additional_fields = {
        'present': 'bool',
        'absent': 'bool',
        'endemism': 'str',
        'sampling_method': 'str',
        'sampling_effort': 'str',
        'reference': 'str',
        'reference_category': 'str',
        'site_description': 'str',
        'site_code': 'str'
    }

    def add_additional_fields(self, fields):
        if not isinstance(fields, list):
            return
        self.additional_fields = fields + self.additional_fields

    def parse_optional_record(self, record, field_type):
        optional_record = None
        if field_type == 'bool':
            optional_record = record == '1'
        elif field_type == 'char':
            optional_record = record.lower()
        elif field_type == 'str':
            optional_record = record
        elif field_type == 'float':
            try:
                optional_record = float(record)
            except ValueError:
                optional_record = 0.0
        elif field_type == 'int':
            try:
                optional_record = int(record)
            except ValueError:
                optional_record = 0
        return optional_record

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['data'] = self.context_data
        self.context_data = dict()
        return self.render_to_response(context)

    def form_valid(self, form):
        form.save(commit=True)
        collection_processed = {
            'added': {
                'count': 0,
                'message': 'records added'
            },
            'duplicated': {
                'count': 0,
                'message': 'not accepted because duplicates'
            },
            'failed': {
                'count': 0,
                'message': 'failed'
            },
            'different_format': {
                'count': 0,
                'message': 'failed due to wrong format'
            }
        }

        # Read csv
        csv_file = form.instance.csv_file

        # disconnect post save handler of location sites
        # it is done from record signal
        models.signals.post_save.disconnect(
            location_site_post_save_handler,
        )
        models.signals.post_save.disconnect(
            collection_post_save_update_cluster,
        )

        location_sites = []
        with open(csv_file.path, 'r') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for record in csv_reader:
                try:
                    print('------------------------------------')
                    print('Processing : %s' % record['species_name'])
                    location_type, status = LocationType.objects.get_or_create(
                        name='PointObservation',
                        allowed_geometry='POINT'
                    )

                    # Optional records for location site
                    optional_site_records = {}

                    # Optional fields and value
                    optional_records = {}

                    if sys.version_info > (3, 0):
                        # Python 3 code in this block
                        optional_fields_iter = self.additional_fields.items()
                    else:
                        # Python 2 code in this block
                        optional_fields_iter = self.additional_fields.\
                            iteritems()

                    for (opt_field, field_type) in optional_fields_iter:
                        if opt_field in record:
                            optional_record = self.parse_optional_record(
                                    record[opt_field],
                                    field_type
                            )
                            if not optional_record:
                                optional_record = ''

                            if opt_field[:4] == 'site':
                                optional_site_records[opt_field] = \
                                    optional_record
                            else:
                                if optional_record:
                                    optional_records[opt_field] = \
                                        optional_record

                    record_point = Point(
                        float(record['longitude']),
                        float(record['latitude']))

                    try:
                        location_site, status = LocationSite.objects.\
                            get_or_create(
                                location_type=location_type,
                                geometry_point=record_point,
                                name=record['location_site']
                            )
                    except LocationSite.MultipleObjectsReturned:
                        location_site = LocationSite.objects.filter(
                            location_type=location_type,
                            geometry_point=record_point,
                            name=record['location_site']
                        )[0]

                    if sys.version_info > (3, 0):
                        optional_site_records_iter = \
                            optional_site_records.items()
                    else:
                        optional_site_records_iter = \
                            optional_site_records.iteritems()

                    for opt_key, opt_val in optional_site_records_iter:
                        setattr(location_site, opt_key, opt_val)
                        location_site.save()

                    location_sites.append(location_site)

                    # Get existed taxon
                    collections = self.collection_record.objects.filter(
                            original_species_name=record['species_name']
                    )

                    taxonomy = None
                    if collections:
                        taxonomy = collections[0].taxonomy

                    # custodian field
                    if 'custodian' in record:
                        optional_records['institution_id'] = \
                            record['custodian']

                    collection_records, created = self.collection_record.\
                        objects.\
                        get_or_create(
                            site=location_site,
                            original_species_name=record['species_name'],
                            category=record['category'].lower(),
                            collection_date=datetime.strptime(
                                    record['date'], '%Y-%m-%d'),
                            collector=record['collector'],
                            notes=record['notes'],
                            taxonomy=taxonomy,
                            owner=self.request.user,
                            **optional_records
                        )

                    if created:
                        print('%s records added' % record['species_name'])
                        collection_processed['added']['count'] += 1
                    else:
                        collection_processed['duplicated']['count'] += 1
                        if not taxonomy:
                            print('Update taxon gbif')
                            update_collection_record(collection_records)

                except KeyError:
                    collection_processed['different_format']['count'] += 1
                except ValueError:
                    collection_processed['failed']['count'] += 1
                print('------------------------------------')

        csv_upload_message = ''

        for processed in collection_processed:
            if collection_processed[processed]['count'] > 0:
                csv_upload_message += '%s %s <br/>' % (
                    collection_processed[processed]['count'],
                    collection_processed[processed]['message']
                )

        if collection_processed['added']['count'] > 0:
            csv_upload_message += 'Verify your records ' \
                                  '<a href="/nonvalidated-user-list/">' \
                                  'here</a> <br/>'

        self.context_data['uploaded'] = csv_upload_message

        # reconnect post save handler of location sites
        models.signals.post_save.connect(
            location_site_post_save_handler,
        )
        models.signals.post_save.connect(
            collection_post_save_update_cluster,
        )

        return JsonResponse({
            'message': self.context_data['uploaded']
        })
