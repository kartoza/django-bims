import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, Http404

from bims.models.boundary import Boundary, BoundaryType
from bims.models.user_boundary import UserBoundary


class LayerUploadView(TemplateView):
    template_name = 'upload_layer.html'
    layer_type_name = ''
    max_upload_size = 5242880  # 5MB in bytes

    def is_exist(self, name: str):
        return False

    def is_valid(self, multi_polygon, name):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super(LayerUploadView, self).get_context_data(**kwargs)
        context['title'] = self.layer_type_name
        return context

    def post(self, request, *args, **kwargs):
        geojson_file = request.FILES.get('geojson_file')
        name = request.POST.get('name')

        if self.is_exist(name):
            message = (f"The layer name '{name}' is already in use. "
                       f"Please choose a different name "
                       "and try uploading again.")
            messages.error(self.request, message, extra_tags='layer_upload')
            return HttpResponseRedirect(request.path_info)

        if geojson_file and geojson_file.size > self.max_upload_size:
            messages.error(request, 'The uploaded file is too large. '
                                    'Please make sure the file size is under 1MB.',
                           extra_tags='layer_upload')
            return HttpResponseRedirect(request.path_info)

        if not geojson_file or not self.layer_type_name:
            raise Http404()

        try:
            geojson_data = json.load(geojson_file)
            geometries = [
                GEOSGeometry(
                    json.dumps(feature['geometry']))
                    for feature in geojson_data.get('features', [])
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

            self.is_valid(multi_polygon, name)

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


class BoundaryUploadView(UserPassesTestMixin, LayerUploadView):
    layer_type_name = 'Boundary'

    def test_func(self):
        return self.request.user.has_perm('bims.add_boundary')

    def is_exist(self, name: str):
        return Boundary.objects.filter(name=name).exists()

    def is_valid(self, multi_polygon, name):
        centroid = multi_polygon.centroid if multi_polygon else None
        boundary_type, _ = BoundaryType.objects.get_or_create(
            name=self.layer_type_name
        )

        boundary = Boundary(
            name=name,
            type=boundary_type,
            geometry=multi_polygon,
            centroid=centroid,
            owner=self.request.user
        )
        boundary.save()


class UserBoundaryUploadView(LoginRequiredMixin, LayerUploadView):
    layer_type_name = 'Polygon'

    def is_exist(self, name: str):
        return UserBoundary.objects.filter(
            name=name,
            user=self.request.user
        ).exists()

    def is_valid(self, multi_polygon, name):
        user_boundary = UserBoundary(
            name=name,
            user=self.request.user,
            geometry=multi_polygon,
        )
        user_boundary.save()
