# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db.models import signals
from bims.models import (
    Boundary,
    BiologicalCollectionRecord,
    SearchProcess,
    collection_post_save_handler
)


class Command(BaseCommand):
    help = 'Remove records outside South Africa'

    def all_boundaries(self, parents):
        """
        Returns all children boundaries
        :param parents: list of parents
        :return: list boundaries
        """
        boundaries = Boundary.objects.filter(
            top_level_boundary__in=parents
        )
        if not boundaries:
            return boundaries
        else:
            return boundaries | self.all_boundaries(boundaries)

    def handle(self, *args, **options):
        sa_boundary = Boundary.objects.filter(
            code_name='ZAF'
        )
        if not sa_boundary.exists():
            print('SA Boundary does not exist')
            return

        signals.post_save.disconnect(
            collection_post_save_handler
        )
        boundaries = self.all_boundaries(
            parents=sa_boundary
        )
        boundaries = boundaries.exclude(
            geometry__isnull=True
        )
        polygon_union = boundaries[0].geometry
        print('Get all SA boundaries')
        for boundary in boundaries[1:]:
            polygon_union = polygon_union.union(boundary.geometry)

        print('Get all records outside SA')
        bio = BiologicalCollectionRecord.objects.filter(
            source_collection='gbif'
        ).exclude(
            site__geometry_point__intersects=polygon_union
        )
        print('Got %s records' % bio.count())
        bio.delete()
        SearchProcess.objects.all().delete()
        signals.post_save.connect(
            collection_post_save_handler
        )
