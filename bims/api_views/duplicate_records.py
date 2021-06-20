import logging
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models import BiologicalCollectionRecord

logger = logging.getLogger('bims')


class DuplicateRecordsApiView(APIView):
    """ Get Duplicate Records"""

    def get(self, *args):

        duplicated = []
        sites = BiologicalCollectionRecord.objects.all().values_list(
            'site_id', flat=True).distinct('site_id')
        for site in sites:
            records_site = BiologicalCollectionRecord.objects.filter(site_id=site)
            if len(records_site) < 2:
                continue
            taxon = records_site.values_list(
                'taxonomy_id', flat=True).distinct('taxonomy_id')
            for taxonomy in taxon:
                records_taxonomy = records_site.filter(taxonomy_id=taxonomy)
                if len(records_taxonomy) < 2:
                    continue
                dates = records_taxonomy.values_list(
                    'collection_date', flat=True).distinct('collection_date')
                for date in dates:
                    records = records_taxonomy.filter(collection_date=date)
                    if len(records) > 1:
                        for record in records:
                            duplicated.append(record)

        return Response({
                'records': duplicated,
        })
