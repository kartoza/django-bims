from datetime import datetime
from braces.views import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
from django.db.models import signals
from django.http import HttpResponseForbidden
from django.apps import apps
from django.contrib.gis.geos import Point

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


class CollectionUploadView(View, LoginRequiredMixin):

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseForbidden()

        try:
            species_name = request.POST['ud_species_name']
            location_site = request.POST['ud_location_site']
            collection_date = request.POST['ud_collection_date']
            collector = request.POST['ud_collector']
            category = request.POST['ud_category']
            notes = request.POST['ud_notes']
            module = request.POST['ud_module']
            lat = request.POST['lat']
            lon = request.POST['lon']

            if module != 'base':
                # Find model
                app_label, model_name = module.split('.')
                collection_model = apps.get_model(
                        app_label=app_label,
                        model_name=model_name
                )
            else:
                collection_model = BiologicalCollectionRecord

            # Deactivate signals
            signals.post_save.disconnect(
                    location_site_post_save_handler,
            )
            signals.post_save.disconnect(
                    collection_post_save_update_cluster,
            )

            # Only point for now
            location_type, status = LocationType.objects.get_or_create(
                    name='PointObservation',
                    allowed_geometry='POINT'
            )
            record_point = Point(float(lon), float(lat))

            location_site, status = LocationSite.objects.get_or_create(
                    location_type=location_type,
                    geometry_point=record_point,
                    name=location_site,
            )

            # Get existed taxon
            existed_collections = collection_model.objects.filter(
                    original_species_name=species_name
            )

            taxon_gbif = None
            if existed_collections:
                taxon_gbif = existed_collections[0].taxon_gbif_id

            collection_record, created = collection_model. \
                objects. \
                get_or_create(
                    site=location_site,
                    original_species_name=species_name,
                    category=category.lower(),
                    collection_date=datetime.strptime(
                            collection_date, '%m/%d/%Y'),
                    collector=collector,
                    notes=notes,
                    taxon_gbif_id=taxon_gbif,
                    owner=self.request.user,
                )

            # reconnect post save handler of location sites
            signals.post_save.connect(
                    location_site_post_save_handler,
            )
            signals.post_save.connect(
                    collection_post_save_update_cluster,
            )

            if created:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Collection added, waiting for validation'})
            else:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'Failed to add collection'
                })
        except KeyError as e:
            return JsonResponse({
                'status': 'failed',
                'message': 'KeyError : ' + str(e)})
