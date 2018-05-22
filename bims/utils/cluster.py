__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '21/05/18'

import logging
from django.db.models import Q
from bims.models.boundary import Boundary
from bims.models.boundary_type import BoundaryType
from bims.models.cluster import Cluster
from bims.models.location_site import LocationSite
from bims.models.survey import Survey

logger = logging.getLogger(__name__)


def update_cluster(biological_collection):
    """
    Update cluster when biological collection has been saved.
    The saving process is getting boundary of biological collection,
    check the number of biological collection in that boundary.
    And also checking number of sites and surveys on that boundary

    Note: biological collection in here is as parent. When model inherit
    biological collection, the cluster module will be the child model.

    :param biological_collection: Biological collection record model
    """
    verbose_name = biological_collection._meta.verbose_name

    # Get all type of boundary
    for boundary_type in BoundaryType.objects.all():
        boundaries = Boundary.objects.filter(
            type=boundary_type
        ).filter(
            geometry__contains=biological_collection.site.get_geometry())

        # Get boundary for each type that
        # contains biological collection records
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
                cluster = Cluster.objects.get(
                    boundary=boundary,
                    module=verbose_name
                )
            except Cluster.DoesNotExist:
                cluster = Cluster()

            cluster.boundary = boundary
            cluster.module = verbose_name
            cluster.site_count = sites.count()
            cluster.survey_count = surveys.count()
            cluster.record_count = records.count()
            cluster.save()

            # logging
            logger.info('CLUSTER : %s, %s' % (
                cluster.boundary, cluster.module))
            logger.info('FOUND site_count: %s' % cluster.site_count)
            logger.info('FOUND survey_count: %s' % cluster.survey_count)
            logger.info('FOUND record_count: %s' % cluster.record_count)
