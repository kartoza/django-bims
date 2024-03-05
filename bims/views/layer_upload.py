import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, Http404

from bims.models.boundary import Boundary, BoundaryType


class LayerUploadView(LoginRequiredMixin, TemplateView):
    template_name = 'upload_layer.html'

    def post(self, request, *args, **kwargs):
        geojson_file = request.FILES.get('geojson_file')
        name = request.POST.get('name')
        boundary_type_name = request.POST.get('boundary_type_name', '')

        if Boundary.objects.filter(name=name).exists():
            message = (f"The layer name '{name}' is already in use. "
                       f"Please choose a different name "
                       "and try uploading again.")
            messages.error(self.request, message, extra_tags='layer_upload')
            return HttpResponseRedirect(request.path_info)

        if not geojson_file or not boundary_type_name:
            raise Http404()

        try:
            geojson_data = json.load(geojson_file)
            geometries = [
                GEOSGeometry(
                    json.dumps(feature['geometry'])) for feature in geojson_data.get('features', [])
            ]
            polygons = []
            for geom in geometries:
                if isinstance(geom, Polygon):
                    polygons.append(geom)
                elif isinstance(geom, MultiPolygon):
                    for poly in geom:
                        if isinstance(poly, Polygon):
                            polygons.append(poly)

            multi_polygon = MultiPolygon(polygons)

            centroid = multi_polygon.centroid if multi_polygon else None
            boundary_type, _ = BoundaryType.objects.get_or_create(
                name=boundary_type_name
            )

            boundary = Boundary(
                name=name,
                type=boundary_type,
                geometry=multi_polygon,
                centroid=centroid,
                owner=self.request.user
            )
            boundary.save()
            messages.success(self.request,
                             'Layer successfully uploaded and saved.',
                             extra_tags='layer_upload')
        except ValueError as e:
            messages.error(self.request, f'Invalid GeoJSON geometry: {str(e)}',
                           extra_tags='layer_upload')
        except Exception as e:
            messages.error(self.request, f'An unexpected error occurred: {str(e)}',
                           extra_tags='layer_upload')

        return HttpResponseRedirect(request.path_info)
