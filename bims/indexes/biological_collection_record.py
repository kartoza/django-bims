# coding=utf-8
from haystack import indexes
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.utils.river_catchments import get_river_catchment_site


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

    vernacular_names = indexes.CharField(
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
        model_attr='is_validated'
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

    taxonomy = indexes.IntegerField(indexed=True)

    taxonomy_not_null = indexes.BooleanField(indexed=True)

    taxon_canonical_name = indexes.NgramField(
        model_attr='taxonomy__canonical_name',
        indexed=True
    )

    taxon_scientific_name = indexes.NgramField(
        model_attr='taxonomy__scientific_name',
        indexed=True
    )

    taxon_canonical_name_exact = indexes.CharField(
        model_attr='taxonomy__canonical_name',
        indexed=True
    )

    taxon_scientific_name_exact = indexes.CharField(
        model_attr='taxonomy__scientific_name',
        indexed=True
    )

    taxon_class = indexes.CharField(
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

    site_id_indexed = indexes.IntegerField(
        indexed=True
    )

    endemism = indexes.CharField(
        indexed=True
    )

    iucn_status = indexes.CharField(
        indexed=True
    )

    river_catchments = indexes.CharField(
        indexed=True
    )

    boundary = indexes.CharField(
        indexed=True
    )

    def prepare_taxon_class(self, obj):
        if obj.taxonomy:
            return obj.taxonomy.class_name
        return ''

    def prepare_site_id_indexed(self, obj):
        if obj.site:
            return obj.site.id
        return 0

    def prepare_taxonomy(self, obj):
        if obj.taxonomy:
            return obj.taxonomy.id
        return 0

    def prepare_taxonomy_not_null(self, obj):
        if obj.taxonomy:
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
        if not obj.site:
            return ''
        if not obj.site.boundary:
            return ''
        ids = []
        boundary = obj.site.boundary
        while True:
            try:
                ids.append(boundary.id)
                boundary = boundary.top_level_boundary
            except AttributeError:
                break
        return '_' + '_'.join([str(i) for i in ids]) + '_'

    def prepare_endemism(self, obj):
        if not obj.taxonomy:
            return ''
        if not obj.taxonomy.endemism:
            return ''
        return obj.taxonomy.endemism.name

    def prepare_iucn_status(self, obj):
        if not obj.taxonomy:
            return ''
        if not obj.taxonomy.iucn_status:
            return ''
        return obj.taxonomy.iucn_status.category

    def prepare_vernacular_names(self, obj):
        if not obj.taxonomy:
            return ''
        return ','.join(obj.taxonomy.vernacular_names.filter(
            language='eng'
        ).values_list('name', flat=True))

    def prepare_river_catchments(self, obj):
        if not obj.site:
            return ''
        if not obj.site.location_context_document:
            return ''
        river_catchment_array = get_river_catchment_site(obj.site)
        river_catchment_string = ''
        for river_catchment in river_catchment_array:
            river_catchment_string += '_'
            river_catchment_string += river_catchment.replace(' ', '_')
            river_catchment_string += '_'
        return river_catchment_string

    class Meta:
        app_label = 'bims'

    def index_queryset(self, using=None):
        """Used to reindex model"""
        return self.get_model().objects.all()

    def get_model(self):
        return BiologicalCollectionRecord
