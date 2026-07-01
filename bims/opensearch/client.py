import logging
from django.conf import settings
from opensearchpy import OpenSearch

logger = logging.getLogger('bims')

_client = None


def get_client() -> OpenSearch:
    global _client
    if _client is None:
        host = getattr(settings, 'OPENSEARCH_HOST', 'localhost')
        port = int(getattr(settings, 'OPENSEARCH_PORT', 9200))
        _client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_compress=True,
            use_ssl=False,
        )
    return _client
