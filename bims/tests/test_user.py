from django.test import TestCase
from bims.tests.model_factories import (
    UserF, BiologicalCollectionRecordF
)
from bims.utils.user import merge_users, get_user
from bims.models import BiologicalCollectionRecord


class TestUser(TestCase):
    """Test all user functions"""

    def setUp(self):
        pass

    def test_merge_users(self):
        """Test a function to merge multiple users"""
        user_1 = UserF.create()
        user_2 = UserF.create()
        BiologicalCollectionRecordF.create(
            owner=user_1,
            collector_user=user_2
        )
        BiologicalCollectionRecordF.create(
            owner=user_2,
            collector_user=user_1
        )
        self.assertTrue(
            BiologicalCollectionRecord.objects.filter(
                owner=user_2
            ).exists()
        )
        merge_users(
            primary_user=user_1,
            user_list=[user_1.id, user_2.id]
        )
        self.assertTrue(
            BiologicalCollectionRecord.objects.filter(
                owner=user_1
            ).count(),
            2
        )
        self.assertTrue(
            BiologicalCollectionRecord.objects.filter(
                collector_user=user_1
            ).count(),
            2
        )
        self.assertFalse(
            BiologicalCollectionRecord.objects.filter(
                owner=user_2
            ).exists()
        )

    def test_get_user_from_username(self):
        username_1 = 'Dimas Ciputra'
        user = get_user(username_1)
        username_2 = 'Dimas T Ciputra'
        user_2 = get_user(username_2)
        self.assertEqual(user, user_2)

        username_3 = 'D_Ciputra'
        user_3 = get_user(username_3)
        username_4 = 'Dim_Ciputra'
        user_4 = get_user(username_4)
        self.assertNotEqual(user_3, user_4)
