from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.cache import cache
from bims.models.dataset import Dataset
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.serializers.dataset_serializer import DatasetSerializer


# Cache key for GBIF dataset keys
GBIF_DATASET_KEYS_CACHE_KEY = 'gbif_dataset_keys'
GBIF_DATASET_KEYS_CACHE_TIMEOUT = 86400  # 24 hours


def clear_dataset_cache():
    """
    Clear the GBIF dataset keys cache.
    Call this function after importing new GBIF data.
    """
    cache.delete(GBIF_DATASET_KEYS_CACHE_KEY)


class DatasetAutocompleteAPIView(APIView):
    """
    Autocomplete API for GBIF datasets.

    Query params:
    - q: search term for dataset name
    - ids: comma-separated database IDs for bootstrapping
    """

    def get(self, request, format=None):
        query = request.query_params.get('q', '')
        ids_param = request.query_params.get('ids', '')

        dataset_keys = cache.get(GBIF_DATASET_KEYS_CACHE_KEY)

        if dataset_keys is None:
            dataset_keys = BiologicalCollectionRecord.objects.filter(
                source_collection='gbif'
            ).exclude(
                dataset_key__isnull=True
            ).values_list('dataset_key', flat=True).distinct()

            dataset_keys = list(filter(None, set(dataset_keys)))
            # Cache for 24 hours
            cache.set(GBIF_DATASET_KEYS_CACHE_KEY, dataset_keys, GBIF_DATASET_KEYS_CACHE_TIMEOUT)

        # Base queryset: only datasets with GBIF records
        base_qs = Dataset.objects.filter(
            uuid__in=dataset_keys
        )

        if ids_param:
            # Bootstrap mode: fetch by database IDs
            ids_list = [int(id.strip()) for id in ids_param.split(',') if id.strip()]
            datasets = base_qs.filter(id__in=ids_list)
        else:
            # Search mode: filter by name
            if len(query) < 2:
                return Response([])
            datasets = base_qs.filter(name__icontains=query).distinct()[:10]

        serializer = DatasetSerializer(datasets, many=True)
        return Response(serializer.data)
