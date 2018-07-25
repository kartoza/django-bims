# coding=utf8

import csv
from django.contrib.gis.db.models import Extent
from django.contrib.gis.geos import Polygon
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.models.taxon import Taxon
from bims.serializers.bio_collection_serializer import (
    BioCollectionSerializer,
    BioCollectionOneRowSerializer
)
from bims.utils.cluster_point import (
    within_bbox,
    overlapping_area,
    update_min_bbox,
    geo_serializer
)


class GetCollectionAbstract(APIView):
    """
    Abstract class for getting collection
    """

    def apply_filter(self, request, ignore_bbox=False):
        # get records with same taxon
        queryset = BiologicalCollectionRecord.objects.filter()
        taxon = request.GET.get('taxon', None)
        if taxon:
            try:
                queryset = queryset.filter(
                    taxon_gbif_id=Taxon.objects.get(pk=taxon)
                )
            except Taxon.DoesNotExist:
                pass

        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(
                original_species_name__contains=search
            )

        # get by bbox
        if not ignore_bbox:
            bbox = request.GET.get('bbox', None)
            if bbox:
                geom_bbox = Polygon.from_bbox(
                    tuple([float(edge) for edge in bbox.split(',')]))
                queryset = queryset.filter(
                    Q(site__geometry_point__intersects=geom_bbox) |
                    Q(site__geometry_line__intersects=geom_bbox) |
                    Q(site__geometry_polygon__intersects=geom_bbox) |
                    Q(site__geometry_multipolygon__intersects=geom_bbox)
                )

        # additional filters
        collector = request.GET.get('collector')
        if collector:
            queryset = queryset.filter(collector=collector)

        category = request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        year_from = request.GET.get('yearFrom')
        if year_from:
            queryset = queryset.filter(
                collection_date__year__gte=year_from)

        year_to = request.GET.get('yearTo')
        if year_to:
            queryset = queryset.filter(
                collection_date__year__lte=year_to)

        months = request.GET.get('months')
        if months:
            months = months.split(',')
            months = [int(month) for month in months]
            queryset = queryset.filter(
                collection_date__month__in=months)
        return queryset


class GetCollectionExtent(GetCollectionAbstract):
    """
    Return extent of collection
    """

    def get(self, request, format=None):
        queryset = self.apply_filter(request, ignore_bbox=True)
        extent = queryset.aggregate(Extent('site__geometry_point'))
        if extent['site__geometry_point__extent']:
            return Response(extent['site__geometry_point__extent'])
        else:
            return Response([])


class CollectionDownloader(GetCollectionAbstract):
    """
    Download all collections with format
    """

    def convert_to_cvs(self, queryset, Model, ModelSerializer):
        """
        Converting data to csv.
        :param queryset: queryset that need to be converted
        :type queryset: QuerySet
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="download.csv"'

        headers = Model._meta.fields
        rows = []
        if queryset:
            serializer = ModelSerializer(
                queryset, many=True)
            headers = serializer.data[0].keys()
            rows = serializer.data

        writer = csv.DictWriter(response, fieldnames=headers)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)

        return response

    def get(self, request):
        file_type = request.GET.get('fileType', None)
        if not file_type:
            file_type = 'csv'
        queryset = self.apply_filter(request, ignore_bbox=True)
        if file_type == 'csv':
            return self.convert_to_cvs(
                queryset,
                BiologicalCollectionRecord,
                BioCollectionOneRowSerializer)
        else:
            return Response([])


class ClusterCollection(GetCollectionAbstract):
    """
    Clustering collection with same taxon
    """

    def clustering_process(
            self, records, zoom, pix_x, pix_y):
        """
        Iterate records and create point clusters
        We use a simple method that for every point, that is not within any
        cluster, calculate it's 'catchment' area and add it to the cluster
        If a point is within a cluster 'catchment' area increase point
        count for that cluster and recalculate clusters minimum bbox

        :param records: list of records.
        :type records: list

        :param zoom: zoom level of map
        :type zoom: int

        :param pix_x: pixel x of icon
        :type pix_x: int

        :param pix_y: pixel y of icon
        :type pix_y: int
        """

        cluster_points = []
        for record in records:
            # get x,y of site
            x = record.site.geometry_point.x
            y = record.site.geometry_point.y

            # check every point in cluster_points
            for pt in cluster_points:
                if 'minbbox' not in pt:
                    pt['minbbox'] = pt['bbox']

                if within_bbox((x, y), pt['minbbox']):
                    # it's in the cluster 'catchment' area
                    pt['count'] += 1
                    pt['minbbox'] = update_min_bbox(
                        (x, y), pt['minbbox'])
                    break

            else:
                # point is not in the catchment area of any cluster
                x_range, y_range = overlapping_area(
                    zoom, pix_x, pix_y, y)
                bbox = (
                    x - x_range * 1.5, y - y_range * 1.5,
                    x + x_range * 1.5, y + y_range * 1.5
                )
                serializer = BioCollectionSerializer(
                    record)
                new_cluster = {
                    'count': 1,
                    'bbox': bbox,
                    'coordinates': [x, y],
                    'record': serializer.data
                }

                cluster_points.append(new_cluster)

        return cluster_points

    def get(self, request, format=None):
        zoom = request.GET.get('zoom', None)
        icon_pixel_x = request.GET.get('icon_pixel_x', None)
        icon_pixel_y = request.GET.get('icon_pixel_y', None)

        if not zoom or not icon_pixel_x or not icon_pixel_y:
            return HttpResponseBadRequest(
                'zoom, icon_pixel_x, and icon_pixel_y need to be '
                'in parameters. '
                'zoom : zoom level of map. '
                'icon_pixel_x: size x of icon in pixel. '
                'icon_pixel_y: size y of icon in pixel. ')
        queryset = self.apply_filter(request)
        cluster = self.clustering_process(
            queryset, int(float(zoom)), int(icon_pixel_x), int(icon_pixel_y)
        )
        return Response(geo_serializer(cluster)['features'])
