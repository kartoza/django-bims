# coding=utf-8
"""Boundary model definition.
"""

import json
from django.contrib.gis.db import models
from bims.models.boundary_type import BoundaryType


class Boundary(models.Model):
    """Boundary model."""

    name = models.CharField(
        max_length=128,
        blank=False,
    )
    code_name = models.CharField(
        max_length=128,
        default="EMPTY"
    )
    type = models.ForeignKey(
        BoundaryType, on_delete=models.CASCADE
    )
    geometry = models.MultiPolygonField(blank=True, null=True)
    centroid = models.PointField(
        null=True,
        blank=True,
    )
    top_level_boundary = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return u'%s - %s' % (
            self.type, self.name)

    class Meta:
        unique_together = ("name", "code_name", "type")

    def get_all_children(self):
        children = [self]
        try:
            child_list = self.children.all()
        except AttributeError:
            return children
        for child in child_list:
            children.extend(child.get_all_children())
        return children

    def generate_cluster(self):
        """ Generate cluster for the boundary.
        This will generate by the rule.
        If the boundary is lowest, it will generate from
        counting record.
        If boundary is not lowest, it will generate from
        calculating cluster of lower boundary
        """
        from bims.models.boundary_type import BoundaryType
        from bims.models.cluster import Cluster
        from bims.utils.cluster import update_cluster

        # get clusters below of this boundary
        clusters = Cluster.objects.filter(
            boundary__top_level_boundary=self).order_by(
            'module'
        )
        # if lowest boundary, do actual update cluster
        if self.type == BoundaryType.lowest_type():
            update_cluster(self)
        else:
            # if not lowest, calculate from it's cluster boundary
            Cluster.objects.filter(
                boundary=self).delete()
            for cluster in clusters:
                # create/update new cluster count
                try:
                    self_cluster = Cluster.objects.get(
                        boundary=self,
                        module=cluster.module
                    )
                except Cluster.DoesNotExist:
                    self_cluster = Cluster.objects.create(
                        boundary=self,
                        module=cluster.module
                    )

                # add site count
                self_cluster.site_count = (
                    self_cluster.site_count + cluster.site_count
                )

                # update detail
                details = {
                    'records': 0,
                    'sites': 0,
                    'survey': 0
                }
                try:
                    details = json.loads(
                        self_cluster.details)
                except ValueError:
                    pass

                # adding value from lower cluster
                try:
                    cluster_detail = json.loads(cluster.details)
                    details['records'] += cluster_detail['records']
                    details['sites'] += cluster_detail['sites']
                    details['survey'] += cluster_detail['survey']
                    try:
                        details['site_detail'] = cluster_detail['site_detail']
                    except KeyError:
                        pass
                except ValueError:
                    pass

                self_cluster.details = json.dumps(details)
                self_cluster.save()
