from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models import (
    BiologicalCollectionRecord,
    TaxonGroup,
    TaxonomicGroupCategory
)



class LandingPageSummary(APIView):
    def get(self, request, *args):
        taxon_groups = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        )
        summary_data = list()
        source_collections = (
            BiologicalCollectionRecord.objects.all().values_list(
                'source_collection', flat=True
            ).distinct('source_collection')
        )

        for taxon_group in taxon_groups:
            _summary_data = {}
            total_all_records = 0
            for source_collection in source_collections:
                total_records = BiologicalCollectionRecord.objects.filter(
                    module_group=taxon_group,
                    source_collection=source_collection
                ).count()
                _summary_data[str(source_collection)] = total_records
                total_all_records += total_records
            summary_data.append({
                'name': taxon_group.name,
                'records': _summary_data,
                'icon': taxon_group.logo.url,
                'total_records': total_all_records,
                'site_visit': BiologicalCollectionRecord.objects.filter(
                    module_group=taxon_group
                ).distinct('survey').count()
            })

        return Response(summary_data)
