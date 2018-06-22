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

    category = indexes.CharField(
            model_attr='category'
    )

    present = indexes.BooleanField(
            model_attr='present'
    )

    absent = indexes.BooleanField(
            model_attr='absent'
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

    class Meta:
        app_label = 'bims'

    def index_queryset(self, using=None):
        """Used to reindex model"""
        return self.get_model().objects.all()

    def get_model(self):
        return BiologicalCollectionRecord
