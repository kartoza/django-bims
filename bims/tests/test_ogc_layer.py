# coding=utf-8
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.utils import timezone

from bims.admin import OgcLayerAdmin
from bims.models import OgcLayer
from bims.models.ogc_layer import (
    OGC_TOKEN_HINT_LENGTH,
    OGC_TOUCH_INTERVAL,
    hash_ogc_token,
)


class TestOgcLayer(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='ogc_owner')

    def _create(self, name='A', **kwargs):
        return OgcLayer.objects.create(name=name, owner=self.user, **kwargs)

    def test_token_is_unique_and_long(self):
        first = self._create('A')
        second = self._create('B')
        self.assertGreaterEqual(len(first.raw_token), 32)
        self.assertNotEqual(first.raw_token, second.raw_token)
        self.assertNotEqual(first.token_hash, second.token_hash)

    def test_only_hash_is_stored(self):
        layer = self._create()
        token = layer.raw_token
        self.assertEqual(layer.token_hash, hash_ogc_token(token))
        layer = OgcLayer.objects.get(pk=layer.pk)
        self.assertIsNone(layer.raw_token)
        self.assertEqual(len(layer.token_hash), 64)
        self.assertNotIn(token, layer.token_hash)

    def test_token_hint_is_end_of_token(self):
        layer = self._create()
        self.assertEqual(len(layer.token_hint), OGC_TOKEN_HINT_LENGTH)
        self.assertTrue(layer.raw_token.endswith(layer.token_hint))

    def test_get_by_token(self):
        layer = self._create()
        self.assertEqual(OgcLayer.get_by_token(layer.raw_token), layer)
        self.assertIsNone(OgcLayer.get_by_token('wrong'))
        self.assertIsNone(OgcLayer.get_by_token(''))
        self.assertIsNone(OgcLayer.get_by_token(None))

    def test_defaults(self):
        layer = self._create()
        self.assertTrue(layer.is_active)
        self.assertFalse(layer.include_sensitive)
        self.assertFalse(layer.include_private)
        self.assertEqual(layer.query, {})
        self.assertIsNone(layer.expires_at)
        self.assertIsNone(layer.last_accessed)

    def test_rotate_token_invalidates_old_one(self):
        layer = self._create()
        old = layer.raw_token
        new = layer.rotate_token()
        self.assertNotEqual(new, old)
        self.assertIsNone(OgcLayer.get_by_token(old))
        self.assertEqual(OgcLayer.get_by_token(new), layer)
        layer.refresh_from_db()
        self.assertEqual(layer.token_hint, new[-OGC_TOKEN_HINT_LENGTH:])

    def test_save_keeps_token(self):
        layer = self._create()
        token = layer.raw_token
        layer.name = 'Renamed'
        layer.save()
        self.assertEqual(OgcLayer.get_by_token(token), layer)

    def test_str_is_name(self):
        self.assertEqual(str(self._create('Fish 2020')), 'Fish 2020')

    def test_token_fields_not_editable(self):
        for name in ('token_hash', 'token_hint'):
            self.assertFalse(OgcLayer._meta.get_field(name).editable)
        self.assertTrue(OgcLayer._meta.get_field('token_hash').unique)

    def test_query_round_trip(self):
        query = {
            'yearFrom': '2010',
            'taxon': '1,2',
            'validated': ['validated']
        }
        layer = self._create(query=query)
        layer.refresh_from_db()
        self.assertEqual(layer.query, query)

    def test_ordered_newest_first(self):
        first = self._create('A')
        second = self._create('B')
        self.assertEqual(list(OgcLayer.objects.all()), [second, first])

    def test_deleted_with_owner(self):
        self._create()
        self.user.delete()
        self.assertEqual(OgcLayer.objects.count(), 0)

    def test_related_name(self):
        self._create()
        self.assertEqual(self.user.ogc_layers.count(), 1)

    def test_settings_defaults(self):
        self.assertEqual(settings.OGC_LAYER_MAX_RECORDS, 100000)
        self.assertEqual(settings.OGC_LAYER_DEFAULT_PAGE_SIZE, 1000)
        self.assertEqual(settings.OGC_LAYER_MAX_PAGE_SIZE, 5000)
        self.assertLessEqual(
            settings.OGC_LAYER_DEFAULT_PAGE_SIZE,
            settings.OGC_LAYER_MAX_PAGE_SIZE)


class TestOgcLayerExpiry(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='ogc_owner')

    def _create(self, **kwargs):
        return OgcLayer.objects.create(name='A', owner=self.user, **kwargs)

    def test_no_expiry_is_never_expired(self):
        layer = self._create()
        self.assertFalse(layer.is_expired)
        self.assertTrue(layer.is_available)

    def test_future_expiry_is_available(self):
        layer = self._create(expires_at=timezone.now() + timedelta(days=1))
        self.assertFalse(layer.is_expired)
        self.assertTrue(layer.is_available)

    def test_past_expiry_is_expired(self):
        layer = self._create(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertTrue(layer.is_expired)
        self.assertFalse(layer.is_available)

    def test_revoked_layer_is_not_available(self):
        layer = self._create(is_active=False)
        self.assertFalse(layer.is_expired)
        self.assertFalse(layer.is_available)


class TestOgcLayerTouch(TestCase):

    def setUp(self):
        user = get_user_model().objects.create(username='ogc_owner')
        self.layer = OgcLayer.objects.create(name='A', owner=user)

    def test_first_touch_writes(self):
        self.assertTrue(self.layer.touch())
        self.layer.refresh_from_db()
        self.assertIsNotNone(self.layer.last_accessed)

    def test_touch_within_interval_is_skipped(self):
        now = timezone.now()
        self.layer.touch(now=now)
        self.assertFalse(self.layer.touch(
            now=now + OGC_TOUCH_INTERVAL - timedelta(seconds=1)))
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.last_accessed, now)

    def test_touch_after_interval_writes(self):
        now = timezone.now()
        self.layer.touch(now=now)
        later = now + OGC_TOUCH_INTERVAL + timedelta(seconds=1)
        self.assertTrue(self.layer.touch(now=later))
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.last_accessed, later)

    def test_touch_does_not_change_token(self):
        token = self.layer.raw_token
        self.layer.touch()
        self.assertEqual(OgcLayer.get_by_token(token), self.layer)


class TestOgcLayerClean(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='ogc_owner')

    def _layer(self, **kwargs):
        return OgcLayer(name='A', owner=self.user, **kwargs)

    def test_valid_layer(self):
        self._layer(query={'taxon': '1'}).clean()

    def test_query_must_be_object(self):
        for bad in ([], 'text', 5, None):
            with self.assertRaises(ValidationError) as ctx:
                self._layer(query=bad).clean()
            self.assertIn('query', ctx.exception.message_dict)

    def test_sensitive_requires_group(self):
        with self.assertRaises(ValidationError) as ctx:
            self._layer(include_sensitive=True).clean()
        self.assertIn('include_sensitive', ctx.exception.message_dict)
        group, _ = Group.objects.get_or_create(name='SensitiveDataGroup')
        self.user.groups.add(group)
        self._layer(include_sensitive=True).clean()

    def test_private_requires_group(self):
        with self.assertRaises(ValidationError) as ctx:
            self._layer(include_private=True).clean()
        self.assertIn('include_private', ctx.exception.message_dict)
        group, _ = Group.objects.get_or_create(name='PrivateDataGroup')
        self.user.groups.add(group)
        self._layer(include_private=True).clean()

    def test_sensitive_group_does_not_allow_private(self):
        group, _ = Group.objects.get_or_create(name='SensitiveDataGroup')
        self.user.groups.add(group)
        with self.assertRaises(ValidationError) as ctx:
            self._layer(include_sensitive=True, include_private=True).clean()
        self.assertNotIn('include_sensitive', ctx.exception.message_dict)
        self.assertIn('include_private', ctx.exception.message_dict)

    def test_clean_without_owner_does_not_crash(self):
        OgcLayer(name='A', include_sensitive=True).clean()


class TestOgcLayerAdmin(TestCase):

    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username='ogc_admin', password='pass', email='a@example.com')
        self.model_admin = OgcLayerAdmin(OgcLayer, AdminSite())
        self.model_admin.message_user = mock.Mock()
        self.request = RequestFactory().post('/')
        self.request.user = self.admin_user
        OgcLayer.objects.create(name='A', owner=self.admin_user)
        OgcLayer.objects.create(name='B', owner=self.admin_user)

    def test_revoke_action(self):
        self.model_admin.revoke(self.request, OgcLayer.objects.all())
        self.assertFalse(OgcLayer.objects.filter(is_active=True).exists())
        self.model_admin.message_user.assert_called_once()

    def test_rotate_token_action(self):
        old_hashes = dict(OgcLayer.objects.values_list('pk', 'token_hash'))
        self.model_admin.rotate_token(self.request, OgcLayer.objects.all())
        for layer in OgcLayer.objects.all():
            self.assertNotEqual(layer.token_hash, old_hashes[layer.pk])
        self.assertEqual(self.model_admin.message_user.call_count, 2)

    def test_token_hint_shown_and_hash_hidden(self):
        self.assertIn('token_hint', self.model_admin.list_display)
        self.assertIn('token_hint', self.model_admin.search_fields)
        form = self.model_admin.get_form(self.request)
        self.assertNotIn('token_hash', form.base_fields)

    def test_actions_registered(self):
        self.assertIn('revoke', self.model_admin.actions)
        self.assertIn('rotate_token', self.model_admin.actions)
