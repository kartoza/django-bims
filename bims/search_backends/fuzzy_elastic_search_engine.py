# coding=utf-8
from bims.search_backends.fuzzy_elastic_backend import FuzzyElasticBackend
from haystack.backends.elasticsearch_backend import ElasticsearchSearchEngine


class FuzzyElasticSearchEngine(ElasticsearchSearchEngine):
    backend = FuzzyElasticBackend
