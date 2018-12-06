import copy
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from bims.models import (
    TaxonGroup,
    Taxonomy,
    BiologicalCollectionRecord,
)
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory


class ModuleSummary(APIView):
    """
    Summary for species module created in TaxonGroup
    """

    def get(self, request, *args):
        response_data = {}
        taxon_groups = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        )

        taxonomy_filter = 'taxonomy__id'
        category = 'category'

        summaries = list(BiologicalCollectionRecord.objects.values(
            taxonomy_filter,
            category
        ).annotate(
            total=Count(taxonomy_filter),
            total_category=Count(category)
        ))

        summaries_unprocessed = copy.deepcopy(summaries)
        for group in taxon_groups:
            response_data[group.name] = {}
            taxon_classes = group.taxonomies.all().values_list(
                'scientific_name', flat=True
            )

            summary_data = {}
            summary_taxonomy_ids = []

            for summary in summaries:
                taxonomy_id = summary[taxonomy_filter]
                if not taxonomy_id:
                    continue

                taxonomy = Taxonomy.objects.get(id=taxonomy_id)
                if not taxonomy:
                    continue

                class_name = taxonomy.class_name
                if not class_name:
                    continue
                if class_name not in taxon_classes:
                    continue
                if class_name not in summary_data:
                    summary_data[class_name] = {
                        'total': 0,
                        'total_site': 0
                    }

                if summary[category] not in summary_data[class_name]:
                    summary_data[class_name][summary[category]] = 0

                summary_data[class_name]['total'] += summary['total']
                summary_data[class_name][summary[category]] += (
                    summary['total_category']
                )

                total_site = len(BiologicalCollectionRecord.objects.filter(
                    taxonomy__id=taxonomy_id
                ).values('site__id').distinct())
                summary_data[class_name]['total_site'] += total_site

                summary_taxonomy_ids.append(taxonomy_id)
                summaries_unprocessed.remove(summary)

            # Count total sites
            for taxon_class in taxon_classes:
                summary_data[taxon_class]['total_site'] = len(
                    BiologicalCollectionRecord.objects.filter(
                        taxonomy__id__in=summary_taxonomy_ids
                    ).values_list('site__id').distinct()
                )

            response_data[group.name] = summary_data
            summaries = summaries_unprocessed

        return Response(response_data)
