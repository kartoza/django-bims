# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from bims.models.cluster import Cluster
from bims.models.boundary import Boundary
from bims.utils.cluster import update_cluster


class Command(BaseCommand):
    help = 'Update all cluster'

    def handle(self, *args, **options):
        Cluster.objects.all().delete()
        for boundary in Boundary.objects.all():
            update_cluster(boundary)
