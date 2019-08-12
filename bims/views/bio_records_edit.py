# coding=utf-8
import json
from braces.views import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import signals
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from bims.forms.bio_records_update import BioRecordsForm
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord,
    collection_post_save_update_cluster
)
from bims.models.location_site import (
    LocationSite,
    location_site_post_save_handler
)
from bims.models.reference_link import ReferenceLink
from bims.models.location_type import LocationType
from bims.utils.get_key import get_key
from bims.permissions.api_permission import AllowedTaxon
from bims.serializers.reference_serializer import ReferenceSerializer
from bims.serializers.document_serializer import DocumentSerializer
from td_biblio.models import Entry
from geonode.documents.models import Document


class BioRecordsUpdateView(LoginRequiredMixin, UpdateView):
    model = BiologicalCollectionRecord
    template_name = 'bio_records_update.html'
    form_class = BioRecordsForm
    success_url = reverse_lazy('nonvalidated-user-list')

    def user_passes_test(self, request):
        if request.user.is_authenticated():
            self.object = self.get_object()
            allowed_taxon = AllowedTaxon()
            taxon_list = allowed_taxon.get(request.user)
            return (
                self.object.owner == request.user or
                self.object.taxonomy in taxon_list or
                self.object.collector_user == request.user
            )
        return False

    def dispatch(self, request, *args, **kwargs):
        if not self.user_passes_test(request):
            raise PermissionDenied
        return super(BioRecordsUpdateView, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(
            BioRecordsUpdateView, self).get_context_data(**kwargs)
        context['geometry_type'] = \
            self.object.site.location_type.allowed_geometry
        if context['geometry_type'] == 'POLYGON':
            context['geometry'] = \
                self.object.site.geometry_polygon.geojson
        elif context['geometry_type'] == 'LINE':
            context['geometry'] = \
                self.object.site.geometry_line.geojson
        else:
            context['geometry'] = \
                self.object.site.geometry_point.geojson

        context['bing_map_key'] = get_key('BING_MAP_KEY')

        context['all_references'] = ReferenceSerializer(
                Entry.objects.all(),
                many=True).data

        reference_links = ReferenceLink.objects.filter(
                collection_record=self.object
        )
        context['references_link'] = []
        for reference in reference_links:
            context['references_link'].append(reference.reference.id)

        documents = self.object.documents.all()
        if documents:
            context['documents_selected'] = DocumentSerializer(
                documents, many=True).data

        context['location_site_selected'] = self.object.site

        return context


    def form_valid(self, form):
        super(BioRecordsUpdateView, self).form_valid(form)
        geometry_type = self.request.POST.get('geometry_type', None)
        geojson = self.request.POST.get('geometry', None)
        references = self.request.POST.get('references', None)
        documents = self.request.POST.get('documents', None)
        features = json.loads(geojson)
        site_id = self.request.POST.get('location_site', None)
        site = LocationSite.objects.get(id=site_id)
        location_site_name = site.name
        if len(features['features']) > 0:
            signals.post_save.disconnect(
                location_site_post_save_handler,
            )
            signals.post_save.disconnect(
                collection_post_save_update_cluster,
            )

            geometry = \
                GEOSGeometry(json.dumps(features['features'][0]['geometry']))

            if geometry_type == 'Polygon':
                location_type, status = LocationType.objects.get_or_create(
                    name='PolygonObservation',
                    allowed_geometry='POLYGON'
                )
                location_site, created = LocationSite.objects.get_or_create(
                    name=location_site_name,
                    geometry_polygon=geometry,
                    location_type=location_type,
                )
            elif geometry_type == 'MultiPolygon':
                location_type, status = LocationType.objects.get_or_create(
                    name='MutiPolygonObservation',
                    allowed_geometry='MULTIPOLYGON'
                )
                location_site, created = LocationSite.objects.get_or_create(
                    name=location_site_name,
                    geometry_multipolygon=geometry,
                    location_type=location_type,
                )
            elif geometry_type == 'LineString':
                location_type, status = LocationType.objects.get_or_create(
                    name='LineObservation',
                    allowed_geometry='LINE'
                )
                location_site, created = LocationSite.objects.get_or_create(
                    name=location_site_name,
                    geometry_line=geometry,
                    location_type=location_type,
                )
            else:
                location_type, status = LocationType.objects.get_or_create(
                    name='PointObservation',
                    allowed_geometry='POINT'
                )
                location_site, created = LocationSite.objects.get_or_create(
                    name=location_site_name,
                    geometry_point=geometry,
                    location_type=location_type,
                )

            self.object.site = location_site
            self.object.save()

            new_reference_link = []
            old_reference_link = ReferenceLink.objects.filter(
                    collection_record=self.object)

            if references:
                references = references.split(',')
                for reference in references:
                    try:
                        entry = Entry.objects.get(id=reference)
                        reference_link, created = ReferenceLink.objects.\
                            get_or_create(
                                collection_record=self.object,
                                reference=entry)
                        new_reference_link.append(reference_link)
                    except Entry.DoesNotExist:
                        pass

            for reference_link in old_reference_link:
                if reference_link not in new_reference_link:
                    reference_link.delete()

            self.object.documents.clear()
            if documents:
                documents = documents.split(',')
                for id_document in documents:
                    try:
                        document = Document.objects.get(
                            id=id_document
                        )
                        self.object.documents.add(document)
                        self.object.save()
                    except Document.DoesNotExist:
                        pass

            # reconnect signals
            signals.post_save.connect(
                location_site_post_save_handler,
            )
            signals.post_save.connect(
                collection_post_save_update_cluster,
            )

        return HttpResponseRedirect(self.success_url)
