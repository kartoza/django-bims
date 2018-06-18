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

    class Meta:
        app_label = 'bims'

    def index_queryset(self, using=None):
        """Used to reindex model"""
        return self.get_model().objects.all()

    def get_model(self):
        return BiologicalCollectionRecord
