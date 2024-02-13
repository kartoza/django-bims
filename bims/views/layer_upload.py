import json

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.views.generic import TemplateView
from django.http import JsonResponse

from bims.models.boundary import Boundary, BoundaryType


class LayerUploadView(TemplateView):
    template_name = 'upload_layer.html'

    def post(self, request, *args, **kwargs):
        geojson_file = request.FILES.get('geojson_file')
        name = request.POST.get('name')
        boundary_type_name = request.POST.get('boundary_type_name', '')

        if not geojson_file or not boundary_type_name:
            return JsonResponse({
                'error': 'No file uploaded'
            }, status=400)

        try:
            geojson_data = json.load(geojson_file)
            geometries = [
                GEOSGeometry(
                    json.dumps(feature['geometry'])) for feature in geojson_data.get('features', [])
            ]
            multi_polygon = MultiPolygon(
                [geom for geom in geometries if isinstance(geom, (MultiPolygon, GEOSGeometry))])

            centroid = multi_polygon.centroid if multi_polygon else None
            boundary_type, _ = BoundaryType.objects.get_or_create(
                name=boundary_type_name
            )

            boundary = Boundary(
                name=name,
                type=boundary_type,
                geometry=multi_polygon,
                centroid=centroid
            )
            boundary.save()

            return JsonResponse(
                {'message': 'Layer successfully uploaded and saved.'},
                status=201)
        except ValueError as e:
            return JsonResponse(
                {'error': f'Invalid GeoJSON geometry: {str(e)}'},
                status=400)
        except Exception as e:
            return JsonResponse(
                {'error': f'An unexpected error occurred: {str(e)}'},
                status=500)
