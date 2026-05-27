# coding=utf-8
"""MetaGroup summary API view."""
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from sorl.thumbnail import get_thumbnail

from bims.enums import TaxonomicStatus
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.models.meta_group import MetaGroup
from bims.models.taxon_group import TaxonGroup
from bims.models import BiologicalCollectionRecord
from bims.models.taxonomy import Taxonomy


class MetaGroupSummary(APIView):
    """
    Returns aggregated summary statistics for each MetaGroup.

    For each metagroup the response contains:
      - id, name, description, gbif_key
      - icon (thumbnail URL of the logo, if set)
      - total_records  – occurrence records across all member modules
      - total_taxa     – distinct accepted taxa across all member modules
      - total_sites    – distinct location sites across all member modules
    """

    def _taxon_group_ids(self, metagroup):
        """Return all TaxonGroup PKs (any level) that belong to this metagroup."""
        top_level_ids = list(
            metagroup.taxon_groups.values_list('id', flat=True)
        )
        all_ids = list(top_level_ids)
        # Walk the hierarchy downward so child modules are included.
        queue = list(top_level_ids)
        while queue:
            children = list(
                TaxonGroup.objects.filter(parent__in=queue).values_list('id', flat=True)
            )
            all_ids.extend(children)
            queue = children
        return all_ids

    def _summary_for_metagroup(self, metagroup):
        group_ids = self._taxon_group_ids(metagroup)

        collections = BiologicalCollectionRecord.objects.filter(
            taxonomy__taxongrouptaxonomy__taxongroup__in=group_ids
        )

        taxa_qs = Taxonomy.objects.filter(
            taxongrouptaxonomy__taxongroup__in=group_ids,
            taxonomic_status=TaxonomicStatus.ACCEPTED.name,
        ).distinct()

        data = {
            'id': metagroup.pk,
            'name': metagroup.name,
            'description': metagroup.description,
            'gbif_key': metagroup.gbif_key,
            'total_records': collections.count(),
            'total_taxa': taxa_qs.count(),
            'total_sites': collections.values('site').distinct().count(),
        }

        if metagroup.logo:
            try:
                data['icon'] = get_thumbnail(
                    metagroup.logo, 'x140', crop='center'
                ).url
            except (ValueError, AttributeError):
                data['icon'] = metagroup.logo.url
        else:
            data['icon'] = None

        return data

    def get(self, request, *args, **kwargs):
        metagroups = MetaGroup.objects.all()
        result = [self._summary_for_metagroup(mg) for mg in metagroups]
        return Response(result)
