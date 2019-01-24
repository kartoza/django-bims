# coding=utf-8
from bims.models.location_site import \
    LocationSite
from haystack import indexes


class LocationSiteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    site_name = indexes.CharField(indexed=True, model_attr='name')
    boundary = indexes.CharField(
        indexed=True
    )

    location_type_name = indexes.NgramField(
        indexed=True,
        model_attr='location_type__name'
    )

    location_site_point = indexes.LocationField()

    location_coordinates = indexes.CharField()

    location_site_name = indexes.CharField(
        model_attr='name'
    )

    location_site_id = indexes.CharField(
        model_attr='id'
    )

    def prepare_location_site_point(self, obj):
        longitude = obj.get_centroid().y
        latitude = obj.get_centroid().x
        longitude = ((longitude + 180) % 360) - 180
        latitude = ((latitude + 180) % 360) - 180
        return '%s,%s' % (longitude, latitude)

    location_site_geometry = indexes.CharField()
    id = indexes.CharField()

    def prepare_location_coordinates(self, obj):
        longitude = obj.get_centroid().y
        latitude = obj.get_centroid().x
        longitude = ((longitude + 180) % 360) - 180
        latitude = ((latitude + 180) % 360) - 180
        return '%s,%s' % (longitude, latitude)

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
        if not obj.boundary:
            return ''
        ids = []
        boundary = obj.boundary
        while True:
            try:
                ids.append(boundary.id)
                boundary = boundary.top_level_boundary
            except AttributeError:
                break
        return '_' + '_'.join([str(i) for i in ids]) + '_'

    class Meta:
        app_label = 'bims'

    def index_queryset(self, using=None):
        """Used to reindex model"""
        return self.get_model().objects.all()

    def get_model(self):
        return LocationSite
