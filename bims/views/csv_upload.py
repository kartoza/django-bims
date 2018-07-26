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
from bims.tasks.collection_record import update_search_index, update_cluster


class CsvUploadView(FormView):
    """Csv upload view."""

    form_class = CsvUploadForm
    template_name = 'csv_uploader.html'
    context_data = dict()
    success_url = reverse_lazy('csv-upload')
    collection_record = BiologicalCollectionRecord

    additional_fields = {
        'present': 'bool',
        'absent': 'bool'
    }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['data'] = self.context_data
        self.context_data = dict()
        return self.render_to_response(context)

    def form_valid(self, form):
        form.save(commit=True)
        collection_processed = {
            'added': 0,
            'failed': 0
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

                    record_point = Point(
                        float(record['longitude']),
                        float(record['latitude']))

                    location_site, status = LocationSite.objects.get_or_create(
                        location_type=location_type,
                        geometry_point=record_point,
                        name=record['location_site'],
                    )
                    location_sites.append(location_site)

                    # Get existed taxon
                    collections = self.collection_record.objects.filter(
                            original_species_name=record['species_name']
                    )

                    taxon_gbif = None
                    if collections:
                        taxon_gbif = collections[0].taxon_gbif_id

                    # Optional fields and value
                    optional_records = {}

                    if (sys.version_info > (3, 0)):
                        # Python 3 code in this block
                        optional_fields_iter = self.additional_fields.items()
                    else:
                        # Python 2 code in this block
                        optional_fields_iter = self.additional_fields.\
                            iteritems()

                    for (opt_field, field_type) in optional_fields_iter:
                        if opt_field in record:
                            if field_type == 'bool':
                                record[opt_field] = record[opt_field] == '1'
                            elif field_type == 'str':
                                record[opt_field] = record[opt_field].lower()
                            optional_records[opt_field] = record[opt_field]

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
                            taxon_gbif_id=taxon_gbif,
                            owner=self.request.user,
                            **optional_records
                        )

                    if created:
                        print('%s Added' % record['species_name'])
                        collection_processed['added'] += 1
                    else:
                        if not taxon_gbif:
                            print('Update taxon gbif')
                            update_collection_record(collection_records)

                except (ValueError, KeyError):
                    collection_processed['failed'] += 1
                print('------------------------------------')

        self.context_data['uploaded'] = 'Collection added ' + \
                                        str(collection_processed['added'])

        # reconnect post save handler of location sites
        models.signals.post_save.connect(
            location_site_post_save_handler,
        )
        models.signals.post_save.connect(
            collection_post_save_update_cluster,
        )

        # Update search index
        update_search_index.delay()

        # Update cluster
        update_cluster.delay()

        return super(CsvUploadView, self).form_valid(form)
