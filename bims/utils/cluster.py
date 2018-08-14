__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '21/05/18'

import json
import logging
from django.db.models import Q
from bims.models.boundary import Boundary, BoundaryType
from bims.models.cluster import Cluster
from bims.tasks.collection_record import update_cluster as task_update_cluster

logger = logging.getLogger(__name__)


def update_cluster(boundary):
    """
    Updating cluster in boundary. It will get all
    biological collection children and generate clustering from that

    :param boundary: boundary that will be checked
    :type boundary: Boundary
    """
    from bims.models.biological_collection_record import (
        BiologicalCollectionRecord
    )
    from bims.models.location_site import LocationSite
    from bims.models.survey import Survey

    records = BiologicalCollectionRecord.objects.filter(validated=True).filter(
        Q(site__geometry_point__intersects=boundary.geometry) |
        Q(site__geometry_line__intersects=boundary.geometry) |
        Q(site__geometry_polygon__intersects=boundary.geometry) |
        Q(site__geometry_multipolygon__intersects=boundary.geometry)
    )
    sites = records.values('site').distinct()

    # get all children model if no CollectionModel given
    verbose_name = LocationSite._meta.verbose_name

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
    details = {
        'records': records.count(),
        'sites': sites.count(),
        'survey': surveys.count()
    }
    cluster.details = json.dumps(details)
    cluster.save()

    # logging
    logger.info('CLUSTER : %s, %s' % (
        cluster.boundary, cluster.module))
    logger.info('FOUND site_count: %s' % cluster.site_count)
    logger.info('DETAILS: %s' % details)


def update_cluster_by_collection(collection):
    """
    Update cluster when collection has been saved.
    The saving process is getting boundary of biological collection,
    check the number of biological collection in that boundary.
    And also checking number of sites and surveys on that boundary

    Note: biological collection in here is as parent. When model inherit
    biological collection, the cluster module will be the child model.

    :param collection: Biological collection record model
    """
    boundary_type = BoundaryType.objects.all().order_by('-level')[0]
    boundaries = Boundary.objects.filter().filter(
        type=boundary_type).filter(
        geometry__contains=collection.site.get_geometry())

    task_update_cluster.delay(boundaries)


def update_cluster_by_site(site):
    """
    Update cluster when site has been saved.
    The saving process is getting boundary of biological collection,
    check the number of biological collection in that boundary.
    And also checking number of sites and surveys on that boundary

    :param site: Site model
    """
    boundaries = Boundary.objects.filter(
        geometry__contains=site.get_geometry()).order_by(
        '-type__level')

    # Update cluster from that boundaries
    for boundary in boundaries:
        boundary.generate_cluster()
