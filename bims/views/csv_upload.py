# coding=utf-8
"""CSV uploader view
"""

import csv
import sys
import uuid
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
    Endemism,
    SamplingMethod
)
from sass.models import (
    River
)
from bims.models.location_site import (
    location_site_post_save_handler
)
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord,
    collection_post_save_update_cluster
)
from bims.utils.gbif import update_collection_record
from bims.location_site.river import allocate_site_codes_from_river


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
        'sampling_effort': 'str',
        'reference': 'str',
        'reference_category': 'str',
        'site_description': 'str',
        'site_code': 'str',
        'source_collection': 'str',
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
                        optional_fields_iter = (
                            self.additional_fields.iteritems()
                        )

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
                        location_site, status = LocationSite.objects. \
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
                            optional_site_records.items()

                    for opt_key, opt_val in optional_site_records_iter:
                        setattr(location_site, opt_key, opt_val)
                        location_site.save()

                    location_sites.append(location_site)

                    # Get existed taxon
                    collections = self.collection_record.objects.filter(
                        original_species_name=record['species_name']
                    )

                    # Endemism
                    endemism = None
                    if 'endemism' in record and record['endemism']:
                        endemism, endemism_created = (
                            Endemism.objects.get_or_create(
                                name=record['endemism']
                            )
                        )

                    taxonomy = None
                    if collections:
                        taxonomy = collections[0].taxonomy

                    if taxonomy:
                        taxonomy.endemism = endemism
                        taxonomy.save()

                    # custodian field
                    if 'custodian' in record:
                        optional_records['institution_id'] = \
                            record['custodian']

                    if 'habitat' in record:
                        habitat_choices = {
                            v: k for k, v in
                            BiologicalCollectionRecord.HABITAT_CHOICES
                        }
                        optional_records['collection_habitat'] = (
                            habitat_choices[record['habitat']]
                        )

                    # sampling method
                    sampling_method = None
                    if 'sampling_method' in record:
                        if record['sampling_method'] != 'unspecified':
                            sampling_method, sm_created = (
                                SamplingMethod.objects.get_or_create(
                                    sampling_method=record['sampling_method']
                                )
                            )
                        optional_records['sampling_method'] = (
                            sampling_method
                        )
                    # sampling effort
                    if sampling_method and 'effort_area' in record:
                        effort_area = record['effort_area']
                        if effort_area:
                            sampling_method.effort_measure = (
                                effort_area + ' m2'
                            )
                            sampling_method.save()
                    if sampling_method and 'effort_time' in record:
                        effort_time = record['effort_time']
                        if effort_time:
                            sampling_method.effort_measure = (
                                effort_time + ' min'
                            )
                            sampling_method.save()

                    # river
                    if 'river' in record and record['river']:
                        river, river_created = River.objects.get_or_create(
                            name=record['river']
                        )
                        location_site.river = river
                        location_site.save()
                        allocate_site_codes_from_river(
                            location_id=location_site.id
                        )

                    if record['date'].lower() == 'unspecified':
                        print('Unspecified date -> Next row')
                        continue

                    created = False
                    collection_records = None
                    if 'uuid' in record and record['uuid']:
                        try:
                            uuid_value = uuid.UUID(record['uuid']).hex
                            collection_records = (
                                BiologicalCollectionRecord.objects.filter(
                                    uuid=uuid_value
                                )
                            )
                            if collection_records.exists():
                                collection_records.update(
                                    site=location_site,
                                    original_species_name=record[
                                        'species_name'
                                    ],
                                    collection_date=datetime.strptime(
                                        record['date'], '%Y-%m-%d'),
                                    taxonomy=taxonomy,
                                )
                                collection_records = collection_records[0]
                            else:
                                optional_records['uuid'] = uuid_value
                        except ValueError:
                            print('Bad uuid format')

                    if not collection_records:
                        collection_records, created = (
                            BiologicalCollectionRecord.objects.get_or_create(
                                site=location_site,
                                original_species_name=record[
                                    'species_name'
                                ],
                                collection_date=datetime.strptime(
                                    record['date'], '%Y-%m-%d'),
                                taxonomy=taxonomy,
                                collector=record['collector'],
                            )
                        )

                    # Additional data
                    additional_data = {}
                    if 'effort_number_throws' in record:
                        additional_data['effort_number_throws'] = (
                            record['effort_number_throws']
                        )
                    if 'catch_per_number' in record:
                        additional_data['catch_per_number'] = (
                            record['catch_per_number']
                        )
                    if 'catch_per_unit_effort' in record:
                        additional_data['catch_per_unit_effort'] = (
                            record['catch_per_unit_effort']
                        )
                    if 'number_of_replicates' in record:
                        additional_data['number_of_replicates'] = (
                            record['number_of_replicates']
                        )
                    if 'hydraulic_biotope' in record:
                        additional_data['hydraulic_biotope'] = (
                            record['hydraulic_biotope']
                        )
                    if 'substratum' in record:
                        additional_data['substratum'] = (
                            record['substratum']
                        )
                    if 'depth_m' in record:
                        additional_data['depth_m'] = (
                            record['depth_m']
                        )
                    if 'near_bed_velocity' in record:
                        additional_data['near_bed_velocity'] = (
                            record['near_bed_velocity']
                        )
                    if 'conductivity' in record:
                        additional_data['conductivity'] = (
                            record['conductivity']
                        )
                    if 'ph' in record:
                        additional_data['ph'] = (
                            record['ph']
                        )
                    if 'dissolved_oxygen' in record:
                        additional_data['dissolved_oxygen'] = (
                            record['dissolved_oxygen']
                        )
                    if 'temperature' in record:
                        additional_data['temperature'] = (
                            record['temperature']
                        )
                    if 'turbidity' in record:
                        additional_data['turbidity'] = (
                            record['turbidity']
                        )

                    collection_records.notes = record['notes']
                    collection_records.owner = self.request.user
                    collection_records.additional_data = additional_data
                    collection_records.save()

                    # update multiple fields
                    BiologicalCollectionRecord.objects.filter(
                        id=collection_records.id
                    ).update(
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
                            collection_records.taxonomy.endemism = endemism
                            collection_records.taxonomy.save()

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
