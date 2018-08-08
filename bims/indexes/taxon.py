# coding=utf-8
from bims.models.taxon import Taxon
from haystack import indexes


class TaxonIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)

    common_name = indexes.NgramField(
            indexed=True,
            model_attr='common_name'
    )

    scientific_name = indexes.NgramField(
            indexed=True,
            model_attr='scientific_name'
    )

    author = indexes.CharField(
            indexed=True,
            model_attr='author'
    )

    iucn_status_category = indexes.CharField(
            indexed=True
    )

    id = indexes.CharField()

    def prepare_iucn_status_category(self, obj):
        if obj.iucn_status:
            return obj.iucn_status.get_status()
        else:
            return ''

    def prepare_id(self, obj):
        if obj.pk:
            return obj.pk
        return ''

    class Meta:
        app_label = 'bims'

    def index_queryset(self, using=None):
        """Used to reindex model"""
        return self.get_model().objects.all()

    def get_model(self):
        return Taxon
