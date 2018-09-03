# coding=utf-8
from bims.models.location_site import \
    LocationSite
from haystack import indexes


class LocationSiteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    site_name = indexes.CharField(indexed=True, model_attr='name')
    boundary = indexes.IntegerField()

    location_type_name = indexes.NgramField(
            indexed=True,
            model_attr='location_type__name'
    )

    location_site_point = indexes.LocationField()

    def prepare_location_site_point(self, obj):
        return '%s,%s' % obj.get_centroid().coords

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

    def prepare_boundary(self, obj):
        if obj.boundary:
            return obj.boundary.id
        return 0

    class Meta:
        app_label = 'bims'

    def index_queryset(self, using=None):
        """Used to reindex model"""
        return self.get_model().objects.all()

    def get_model(self):
        return LocationSite
