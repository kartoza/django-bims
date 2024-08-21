from django_tenants.test.cases import FastTenantTestCase

from bims.models.record_type import merge_record_types
from bims.tests.model_factories import (
    RecordTypeF,
    BiologicalCollectionRecordF,
    BiologicalCollectionRecord,
    RecordType
)


class TestRecordType(FastTenantTestCase):
    def test_merge_record_type(self):
        """
        Tests merge record_type
        """

        record_type_1 = RecordTypeF(name='record_type_test')
        record_type_2 = RecordTypeF(name='record_type_test')
        record_type_3 = RecordTypeF(name='record_type_test')

        BiologicalCollectionRecordF(
            record_type=record_type_2
        )
        BiologicalCollectionRecordF(
            record_type=record_type_3
        )

        merge_record_types(
            primary_record_type=record_type_1,
            record_type_list=RecordType.objects.filter(
                name='record_type_test'
            )
        )

        self.assertEqual(
            BiologicalCollectionRecord.objects.filter(
                record_type=record_type_1
            ).count(),
            2
        )

        self.assertFalse(
            BiologicalCollectionRecord.objects.filter(
                record_type=record_type_2
            ).exists()
        )
