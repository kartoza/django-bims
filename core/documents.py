# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '05/06/18'

from django_elasticsearch_dsl import DocType, Index
from bims.models.biological_collection_record import BiologicalCollectionRecord
from example.models.rock_collection_record import RockCollectionRecord


biological_collection_record = Index('biological_collection_record')
biological_collection_record.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@biological_collection_record.doc_type
class BiologicalCollectionRecordDocument(DocType):
    class Meta:
        model = RockCollectionRecord

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'rock_name',
            'original_species_name',
        ]
