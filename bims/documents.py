# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '05/06/18'

from django_elasticsearch_dsl import DocType, Index
from bims.models.biological_collection_record import BiologicalCollectionRecord


biological_collection_record = Index('biological_collection_record')


@biological_collection_record.doc_type
class BiologicalCollectionRecordDocument(DocType):

    class Meta:
        model = BiologicalCollectionRecord

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'original_species_name',
            'collection_date',
            'collector',
        ]
