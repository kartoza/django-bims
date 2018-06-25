# coding=utf-8
"""CSV uploader view
"""

import csv
from datetime import datetime
from django.urls import reverse_lazy
from django.contrib.gis.geos import Point
from django.views.generic import FormView
from bims.forms.csv_upload import CsvUploadForm
from bims.models import (
    LocationSite,
    LocationType,
)
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord


class CsvUploadView(FormView):
    """Csv upload view."""

    form_class = CsvUploadForm
    template_name = 'csv_uploader.html'
    context_data = dict()
    success_url = reverse_lazy('csv-upload')

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

        with open(csv_file.path, newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for record in csv_reader:
                try:
                    location_type, status = LocationType.objects.get_or_create(
                            name='RiverPointObservation',
                            allowed_geometry='POINT'
                    )

                    record_point = Point(
                            float(record['Longitude']),
                            float(record['Latitude']))

                    location_site, status = LocationSite.objects.get_or_create(
                        location_type=location_type,
                        geometry_point=record_point,
                        name=record['River'],
                    )

                    # Get existed taxon
                    collections = BiologicalCollectionRecord.objects.filter(
                            original_species_name=record['Species']
                    )

                    taxon_gbif = None
                    if collections:
                        taxon_gbif = collections[0].taxon_gbif_id

                    collection, collection_status = \
                        BiologicalCollectionRecord.\
                        objects.get_or_create(
                            site=location_site,
                            original_species_name=record['Species'],
                            category=record['Category'].lower(),
                            present=record['Present'] == 1,
                            absent=record['Absent'] == 1,
                            collection_date=datetime(
                                    int(record['Year']), 1, 1),
                            collector=record['Collector'],
                            notes=record['Notes'],
                            taxon_gbif_id=taxon_gbif,
                        )
                    if collection_status:
                        collection_processed['added'] += 1
                except (ValueError, KeyError):
                    collection_processed['failed'] += 1

        self.context_data['uploaded'] = 'Collection added ' + \
                                        str(collection_processed['added'])
        return super(CsvUploadView, self).form_valid(form)
