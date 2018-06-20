# coding=utf-8
from bims.models.location_site import \
    LocationSite
from haystack import indexes


class LocationSiteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.NgramField(indexed=True, model_attr='name')

    class Meta:
        app_label = 'bims'

    def index_queryset(self, using=None):
        """Used to reindex model"""
        return self.get_model().objects.all()

    def get_model(self):
        return LocationSite
