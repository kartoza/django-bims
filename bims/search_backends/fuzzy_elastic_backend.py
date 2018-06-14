# coding=utf-8
from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend
from django.conf import settings


class FuzzyElasticBackend(ElasticsearchSearchBackend):

    def __init__(self, connection_alias, **connection_options):
        super(FuzzyElasticBackend, self).__init__(
            connection_alias, **connection_options)

    def build_schema(self, fields):
        content_field_name, mapping = super(
            FuzzyElasticBackend, self).build_schema(fields)
        return content_field_name, mapping

    def build_search_kwargs(self, query_string, **kwargs):
        """Build search kwargs with fuzziness.
        """
        search_kwargs = super(FuzzyElasticBackend, self).build_search_kwargs(
            query_string, **kwargs)

        try:
            search_kwargs["sort"]
        except KeyError:
            search_kwargs["sort"] = [{
                "_score": {
                    "order": "desc"
                }
            }]

        if 'query_string' in search_kwargs['query']['filtered']['query']:
            if 'min_score' not in search_kwargs:
                search_kwargs["min_score"] = settings.ELASTIC_MIN_SCORE

            search_kwargs['query']['filtered']['query']['query_string'][
                'fuzziness'] = 'AUTO'
            search_kwargs['query']['filtered']['query']['query_string'][
                'default_operator'] = 'OR'

        return search_kwargs

    def search(self, query_string, **kwargs):
        search = super(
                FuzzyElasticBackend, self
        ).search(query_string, **kwargs)
        return search
