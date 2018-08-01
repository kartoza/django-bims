__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '21/05/18'

import json
import logging
from django.core.exceptions import FieldError
from django.db.models import Q
from bims.models.boundary import Boundary
from bims.models.cluster import Cluster
from bims.tasks.collection_record import update_cluster as task_update_cluster

logger = logging.getLogger(__name__)


def update_cluster(boundary, CollectionModel=None):
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

    sites = BiologicalCollectionRecord.objects.filter(validated=True).filter(
        Q(site__geometry_point__intersects=boundary.geometry) |
        Q(site__geometry_line__intersects=boundary.geometry) |
        Q(site__geometry_polygon__intersects=boundary.geometry) |
        Q(site__geometry_multipolygon__intersects=boundary.geometry)
    ).values('site').distinct()

    # get all children model if no CollectionModel given
    if not CollectionModel:
        children_models = BiologicalCollectionRecord.get_children_model()
        if len(children_models) == 0:
            children_models.append(BiologicalCollectionRecord)
        children_models.append(LocationSite)
    else:
        children_models = [CollectionModel]

    for children_model in children_models:
        verbose_name = children_model._meta.verbose_name
        try:
            records = children_model.objects.filter(
                site__in=sites,
                validated=True)
            sites_with_collection = records
        except FieldError:
            records = children_model.objects.filter(
                id__in=sites)
            sites_with_collection = records

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
            'sites': len(sites_with_collection),
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
    boundaries = Boundary.objects.filter(
        geometry__contains=collection.site.get_geometry()).order_by(
        '-type__level').values_list('id', flat=True)
    boundaries = list(boundaries)
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
