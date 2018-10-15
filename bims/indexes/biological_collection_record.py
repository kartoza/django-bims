# coding=utf-8
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from haystack import indexes


class BiologicalCollectionIndex(indexes.SearchIndex, indexes.Indexable):
    model_pk = indexes.IntegerField(model_attr='pk')
    id = indexes.CharField()
    text = indexes.CharField(document=True, use_template=True)

    original_species_name = indexes.NgramField(
        model_attr='original_species_name',
        indexed=True
    )

    original_species_name_exact = indexes.CharField(
        model_attr='original_species_name',
        indexed=True
    )

    collector = indexes.NgramField(
        model_attr='collector',
        indexed=True
    )

    collection_date_year = indexes.IntegerField(
        model_attr='collection_date__year',
        indexed=True
    )

    collection_date_month = indexes.IntegerField(
        model_attr='collection_date__month',
        indexed=True
    )

    category = indexes.CharField(
        model_attr='category'
    )

    present = indexes.BooleanField(
        model_attr='present'
    )

    absent = indexes.BooleanField(
        model_attr='absent'
    )

    validated = indexes.BooleanField(
        model_attr='validated'
    )

    collection_date = indexes.DateField(
        model_attr='collection_date'
    )

    owner = indexes.CharField(
        model_attr='owner__username'
    )

    notes = indexes.CharField(
        model_attr='notes'
    )

    location_site_name = indexes.CharField(
        model_attr='site__name',
        indexed=True
    )

    location_site_id = indexes.CharField(
        model_attr='site__id'
    )

    location_center = indexes.LocationField()

    location_coordinates = indexes.CharField()

    taxon_gbif = indexes.IntegerField(indexed=True)

    taxon_gbif_not_null = indexes.BooleanField(indexed=True)

    taxon_common_name = indexes.NgramField(
        model_attr='taxon_gbif_id__common_name',
        indexed=True
    )

    taxon_scientific_name = indexes.NgramField(
        model_attr='taxon_gbif_id__scientific_name',
        indexed=True
    )

    taxon_common_name_exact = indexes.CharField(
        model_attr='taxon_gbif_id__common_name',
        indexed=True
    )

    taxon_scientific_name_exact = indexes.CharField(
        model_attr='taxon_gbif_id__scientific_name',
        indexed=True
    )

    taxon_class = indexes.NgramField(
        model_attr='taxon_gbif_id__taxon_class',
        indexed=True
    )

    reference_category = indexes.CharField(
        model_attr='reference_category',
        indexed=True
    )

    reference = indexes.CharField(
        model_attr='reference',
        indexed=True
    )

    boundary = indexes.IntegerField()

    def prepare_taxon_gbif(self, obj):
        if obj.taxon_gbif_id:
            return obj.taxon_gbif_id.id
        return 0

    def prepare_taxon_gbif_not_null(self, obj):
        if obj.taxon_gbif_id:
            return True
        return False

    def prepare_location_center(self, obj):
        if obj.site:
            return '%s,%s' % obj.site.get_centroid().coords
        return '0,0'

    def prepare_location_coordinates(self, obj):
        if obj.site:
            return '%s,%s' % obj.site.get_centroid().coords
        return '0,0'

    def prepare_boundary(self, obj):
        if obj.site.boundary:
            return obj.site.boundary.id
        return 0

    class Meta:
        app_label = 'bims'

    def index_queryset(self, using=None):
        """Used to reindex model"""
        return self.get_model().objects.all()

    def get_model(self):
        return BiologicalCollectionRecord
