# coding=utf-8
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from haystack import indexes


class BiologicalCollectionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    original_species_name = indexes.NgramField(
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
        model_attr='collection_date__month'
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
        model_attr='site__name'
    )

    id = indexes.CharField()

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
        return BiologicalCollectionRecord
