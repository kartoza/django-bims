# coding=utf-8
from bims.models import Taxonomy, BiologicalCollectionRecord
from haystack import indexes


class TaxonIndex(indexes.SearchIndex, indexes.Indexable):
    model_pk = indexes.IntegerField(model_attr='pk')
    text = indexes.EdgeNgramField(document=True, use_template=True)

    canonical_name = indexes.NgramField(
            indexed=True,
            model_attr='canonical_name'
    )

    canonical_name_char = indexes.CharField(
        indexed=True,
        model_attr='canonical_name'
    )

    scientific_name = indexes.NgramField(
            indexed=True,
            model_attr='scientific_name'
    )

    scientific_name_auto = indexes.EdgeNgramField(
            model_attr='scientific_name'
    )

    canonical_name_auto = indexes.EdgeNgramField(
            model_attr='canonical_name'
    )

    author = indexes.CharField(
            indexed=True,
            model_attr='author',
            null=True
    )

    iucn_status_category = indexes.CharField(
            indexed=True
    )

    id = indexes.IntegerField(indexed=True)

    validated_collections = indexes.CharField()

    def prepare_validated_collections(self, obj):
        bios = BiologicalCollectionRecord.objects.filter(
                taxonomy=obj.pk,
                validated=True
        ).values_list('pk', flat=True).distinct()
        return ','.join(str(bio) for bio in bios)

    def prepare_iucn_status_category(self, obj):
        if obj.iucn_status:
            return obj.iucn_status.get_status()
        else:
            return ''

    def prepare_id(self, obj):
        if obj.pk:
            return obj.pk
        return 0

    class Meta:
        app_label = 'bims'

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

    def get_model(self):
        return Taxonomy
