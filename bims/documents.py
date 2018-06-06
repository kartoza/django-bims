# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '05/06/18'

from django_elasticsearch_dsl import DocType, Index, fields
from bims.models.biological_collection_record import BiologicalCollectionRecord
from example.models.rock_collection_record import RockCollectionRecord


biological_collection_record = Index('biological_collection_record')
biological_collection_record.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@biological_collection_record.doc_type
class BiologicalCollectionRecordDocument(DocType):
    original_species_name = fields.TextField()

    class Meta:
        model = BiologicalCollectionRecord

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'original_species_name',
        ]
