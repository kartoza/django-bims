# coding=utf-8
from bims.models.location_site import \
    LocationSite
from haystack import indexes


class LocationSiteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.NgramField(indexed=True, model_attr='name')

    location_type_name = indexes.NgramField(
            indexed=True,
            model_attr='location_type__name'
    )
    location_site_point = indexes.LocationField(
            model_attr='geometry_point'
    )
    location_site_geometry = indexes.CharField()
    id = indexes.CharField()

    def prepare_location_site_geometry(self, obj):
        geometry = obj.get_geometry()
        if geometry:
            return geometry.json
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
        return LocationSite
