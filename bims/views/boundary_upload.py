import os
import json
import sys
from django.views import View
from django.shortcuts import render
from django.db.models import signals
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
from django.views.decorators.csrf import csrf_exempt
from bims.models.user_boundary import UserBoundary

from bims.forms.shapefile_upload import ShapefileUploadForm
from bims.models.shapefile import Shapefile
from bims.models.shapefile_upload_session import ShapefileUploadSession
from bims.uploader.shapefile_extractor import extract_shape_file
from bims.models.location_site import (
    location_site_post_save_handler
)
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord,
    collection_post_save_update_cluster
)
from bims.models.location_site import LocationSite
from bims.models.location_type import LocationType


class ShapefileUploadView(UserPassesTestMixin, LoginRequiredMixin, View):

    template_name = 'shapefile_uploader.html'

    def test_func(self):
        return self.request.user.has_perm('bims.can_upload_shapefile')

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to upload Shapefile')
        return super(ShapefileUploadView, self).handle_no_permission()

    def get(self, request):
        return render(self.request, template_name=self.template_name)

    def post(self, request):
        form = ShapefileUploadForm(
                self.request.POST,
                self.request.FILES,
        )
        if form.is_valid():
            form.token = self.request.POST['csrfmiddlewaretoken']
            shapefile = form.save()
            data = {
                'is_valid': True,
                'name': shapefile.filename,
                'url': shapefile.fileurl}
        else:
            data = {
                'is_valid': False
            }
        return JsonResponse(data)


def process_user_boundary_shapefiles(request):
    from bims.models import UserBoundary
    from django.contrib.gis.geos import Polygon, MultiPolygon
    token = request.GET.get('token', None)
    boundary_name = request.GET.get('name', None)

    if not token:
        return JsonResponse({
            'message': 'empty token'
        })

    shapefiles = Shapefile.objects.filter(
            token=token
    )

    for shp in shapefiles:
        shp.token = ''
        shp.save()

    upload_session, created = ShapefileUploadSession.objects.get_or_create(
            uploader=request.user,
            token=token,
            processed=False,
    )

    if created:
        upload_session.shapefiles = shapefiles
        upload_session.save()

    all_shapefiles = upload_session.shapefiles.all()

    needed_ext = ['.shx', '.shp', '.dbf']
    needed_files = {}

    # Check all needed files
    for shp in all_shapefiles:
        name, extension = os.path.splitext(shp.filename)
        if extension in needed_ext:
            needed_files[extension[1:]] = shp
            needed_ext.remove(extension)

    if len(needed_ext) > 0:
        data = {
            'message': 'missing %s' % ','.join(needed_ext)
        }
        upload_session.error = data['message']
        upload_session.save()
        return JsonResponse(data)

    # Extract shapefile into dictionary
    outputs = extract_shape_file(
            shp_file=needed_files['shp'].shapefile,
            shx_file=needed_files['shx'].shapefile,
            dbf_file=needed_files['dbf'].shapefile,
    )

    geometry = None
    geometries = []

    for geojson in outputs:
        try:
            properties = geojson['properties']

            if not boundary_name:
                if 'name' in properties:
                    boundary_name = properties['name']
                else:
                    boundary_name, extension = os.path.splitext(
                            all_shapefiles[0].filename
                    )

            geojson_json = json.dumps(geojson['geometry'])
            geometry = GEOSGeometry(geojson_json)

            if isinstance(geometry, Polygon):
                geometries.append(geometry)
            elif not isinstance(geometry, MultiPolygon):
                response_message = 'Only polygon and multipolygon allowed'
                upload_session.error = response_message
                upload_session.save()
                return JsonResponse({'message': response_message})

        except (ValueError, KeyError, TypeError) as e:
            upload_session.error = str(e)
            upload_session.save()
            response_message = 'Failed : %s' % str(e)
            return JsonResponse({'message': response_message})

    if len(geometries) > 0:
        geometry = MultiPolygon(geometries)

    user_boundary, created = UserBoundary.objects.get_or_create(
            user=request.user,
            name=boundary_name,
            geometry=geometry
    )
    upload_session.processed = True
    upload_session.save()

    if created:
        response_message = 'User boundary added'
    else:
        response_message = 'User boundary already exists'

    data = {
        'message': response_message
    }
    return JsonResponse(data)


def process_shapefiles(request,
                       collection=BiologicalCollectionRecord,
                       additional_fields=None):
    token = request.GET.get('token', None)

    if not token:
        return JsonResponse({'message': 'empty token'})

    shapefiles = Shapefile.objects.filter(
            token=token
    )

    if not additional_fields:
        additional_fields = {
            'present': 'bool',
        }

    for shp in shapefiles:
        shp.token = ''
        shp.save()

    upload_session, created = ShapefileUploadSession.objects.get_or_create(
            uploader=request.user,
            token=token,
            processed=False,
    )

    if created:
        upload_session.shapefiles = shapefiles
        upload_session.save()

    all_shapefiles = upload_session.shapefiles.all()

    needed_ext = ['.shx', '.shp', '.dbf']
    needed_files = {}

    # Check all needed files
    for shp in all_shapefiles:
        name, extension = os.path.splitext(shp.filename)
        if extension in needed_ext:
            needed_files[extension[1:]] = shp
            needed_ext.remove(extension)

    if len(needed_ext) > 0:
        data = {
            'message': 'missing %s' % ','.join(needed_ext)
        }
        upload_session.error = data['message']
        upload_session.save()
        return JsonResponse(data)

    # Extract shapefile into dictionary
    outputs = extract_shape_file(
            shp_file=needed_files['shp'].shapefile,
            shx_file=needed_files['shx'].shapefile,
            dbf_file=needed_files['dbf'].shapefile,
    )

    # disconnect post save handler of location sites
    # it is done from record signal
    signals.post_save.disconnect(
            location_site_post_save_handler,
    )
    signals.post_save.disconnect(
            collection_post_save_update_cluster,
    )

    collection_added = 0

    for geojson in outputs:
        try:
            # Optional fields and value
            location_site_name = geojson['properties']['location']
            properties = geojson['properties']
            geojson_json = json.dumps(geojson['geometry'])
            geometry = GEOSGeometry(geojson_json)
            optional_records = {}

            if (sys.version_info > (3, 0)):
                # Python 3 code in this block
                optional_fields_iter = additional_fields.items()
            else:
                # Python 2 code in this block
                optional_fields_iter = additional_fields. \
                    iteritems()

            for (opt_field, field_type) in optional_fields_iter:
                if opt_field in properties:
                    if field_type == 'bool':
                        properties[opt_field] = properties[opt_field] == 1
                    elif field_type == 'str':
                        properties[opt_field] = properties[opt_field].lower()
                    optional_records[opt_field] = properties[opt_field]

            # Add custodian
            if 'custodian' in properties:
                optional_records['institution_id'] = properties['custodian']

            if geojson['geometry']['type'] == 'Polygon':
                location_type, status = LocationType.objects.get_or_create(
                        name='PolygonObservation',
                        allowed_geometry='POLYGON'
                )
                location_site, created = LocationSite.objects.get_or_create(
                        name=location_site_name,
                        geometry_polygon=geometry,
                        location_type=location_type,
                )
            elif geojson['geometry']['type'] == 'MultiPolygon':
                location_type, status = LocationType.objects.get_or_create(
                        name='MutiPolygonObservation',
                        allowed_geometry='MULTIPOLYGON'
                )
                location_site, created = LocationSite.objects.get_or_create(
                        name=location_site_name,
                        geometry_multipolygon=geometry,
                        location_type=location_type,
                )
            elif geojson['geometry']['type'] == 'LineString':
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

            collections = collection.objects.filter(
                    original_species_name=properties['species']
            )

            taxonomy = None
            if collections:
                taxonomy = collections[0].taxonomy

            collection_records, created = collection. \
                objects. \
                get_or_create(
                    site=location_site,
                    original_species_name=properties['species'],
                    category=properties['category'].lower(),
                    collection_date=properties['date'],
                    collector=properties['collector'],
                    notes=properties['notes'],
                    taxonomy=taxonomy,
                    owner=request.user,
                    **optional_records)

            if created:
                collection_added += 1

            upload_session.processed = True
            upload_session.save()

        except (ValueError, KeyError) as e:
            upload_session.error = str(e)
            upload_session.save()

    # reconnect signals
    signals.post_save.connect(
            location_site_post_save_handler,
    )
    signals.post_save.connect(
            collection_post_save_update_cluster,
    )

    response_message = 'Added %s records <br/>' % collection_added
    if collection_added > 0:
        response_message += 'Verify your records ' \
                            '<a href="/nonvalidated-user-list/">' \
                            'here</a> <br/>'
    data = {
        'message': response_message
    }
    return JsonResponse(data)


def process_user_boundary_geojson(request):
    if request.method != 'POST':
        return JsonResponse({
            'message': 'Only POST requests are allowed'
        }, status=405)

    try:
        geojson_data = json.loads(
            request.POST.get('geojson', '{}'))
    except json.JSONDecodeError:
        return JsonResponse({
            'message': 'Invalid JSON'}, status=400)

    if not geojson_data.get('features'):
        raise Http404(
            'No features found in GeoJSON')

    boundary_name = request.POST.get('name')
    geometries = []

    for feature in geojson_data['features']:
        geometry = GEOSGeometry(json.dumps(feature['geometry']))

        if not isinstance(geometry, (Polygon, MultiPolygon)):
            return JsonResponse(
                {'message': 'Only polygon and multipolygon allowed'
                 }, status=400)

        if not boundary_name:
            boundary_name = feature.get(
                'properties', {}
            ).get('name', boundary_name)

        geometries.append(geometry)

    if not geometries:
        return JsonResponse({
            'message': 'No valid geometries found'
        }, status=400)

    # Combine geometries into a single MultiPolygon if there are multiple geometries
    geometry = MultiPolygon(geometries)

    user_boundary, created = UserBoundary.objects.get_or_create(
        user_id=request.user.id,
        name=boundary_name,
        defaults={
            'geometry': geometry
        }
    )

    response_message = (
        'User boundary added'
        if created else
        'User boundary already exists'
    )
    return JsonResponse({'message': response_message})
