__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '21/05/18'

from django.db.models import Q
from bims.models.boundary import Boundary
from bims.models.boundary_type import BoundaryType
from bims.models.biological_collection_cluster import (
    BiologicalCollectionCluster
)
from bims.models.location_site import LocationSite
from bims.models.survey import Survey


def update_biological_collection_cluster(biological_collection):
    """
    Update Biological collection cluster.
    :param biological_collection: Biological collection record model
    """
    verbose_name = biological_collection._meta.verbose_name

    # Get all type of boundary
    for boundary_type in BoundaryType.objects.all():
        boundaries = Boundary.objects.filter(
            type=boundary_type
        ).filter(
            geometry__contains=biological_collection.site.get_geometry())

        # Get boundary in each type that in biological collection location
        for boundary in boundaries:
            sites = LocationSite.objects.filter(
                Q(geometry_point__intersects=boundary.geometry) |
                Q(geometry_line__intersects=boundary.geometry) |
                Q(geometry_polygon__intersects=boundary.geometry) |
                Q(geometry_multipolygon__intersects=boundary.geometry)
            )
            records = type(
                biological_collection).objects.filter(
                site__in=sites)
            surveys = Survey.objects.filter(sites__in=sites)

            # create/update new cluster count
            try:
                cluster = BiologicalCollectionCluster.objects.get(
                    boundary=boundary,
                    module=verbose_name
                )
            except BiologicalCollectionCluster.DoesNotExist:
                cluster = BiologicalCollectionCluster()

            cluster.boundary = boundary
            cluster.module = verbose_name
            cluster.site_count = sites.count()
            cluster.survey_count = surveys.count()
            cluster.record_count = records.count()
            print('CLUSTER : %s, %s' % (
                cluster.boundary, cluster.module))
            print('FOUND site_count: %s' % cluster.site_count)
            print('FOUND survey_count: %s' % cluster.survey_count)
            print('FOUND record_count: %s' % cluster.record_count)
            cluster.save()
