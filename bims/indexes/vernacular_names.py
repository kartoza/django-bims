# coding=utf-8
from bims.models import VernacularName
from haystack import indexes


class VernacularNameIndex(indexes.SearchIndex, indexes.Indexable):
    model_pk = indexes.IntegerField(model_attr='pk')
    text = indexes.EdgeNgramField(document=True, use_template=True)
    id = indexes.IntegerField(indexed=True)

    name = indexes.NgramField(
        indexed=True,
        model_attr='name'
    )

    lang = indexes.CharField(
        indexed=True,
        model_attr='language'
    )

    class Meta:
        app_label = 'bims'

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

    def get_model(self):
        return VernacularName

    def prepare_id(self, obj):
        if obj.pk:
            return obj.pk
        return 0
