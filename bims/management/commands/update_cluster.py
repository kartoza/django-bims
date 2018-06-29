# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from bims.models.cluster import Cluster
from bims.models.boundary import Boundary
from bims.models.boundary_type import BoundaryType
from bims.utils.cluster import update_cluster


class Command(BaseCommand):
    help = 'Update all cluster'

    def handle(self, *args, **options):
        lowest_type = BoundaryType.lowest_type()
        # Cluster.objects.all().delete()
        for boundary_type in BoundaryType.objects.all().order_by('-level'):
            for boundary in Boundary.objects.filter(type=boundary_type):
                print 'generate cluster for %s' % boundary
                boundary.generate_cluster()
