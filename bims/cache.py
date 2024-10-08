from django.db import models
from django.core.cache import cache
from django.db.models.query import QuerySet

LANDING_PAGE_MODULE_SUMMARY_CACHE = 'LANDING_PAGE_MODULE_SUMMARY_CACHE'
UPDATE_FILTERS_CACHE = 'UPDATE_FILTERS'
HARVESTING_GEOCONTEXT = 'HARVESTING_GEOCONTEXT_3'


def instance_cache_key(instance):
    opts = instance._meta
    if hasattr(opts, 'model_name'):
        name = opts.model_name
    else:
        name = opts.module_name
    return '%s.%s:%s' % (opts.app_label, name, instance.pk)


class CacheQuerySet(QuerySet):
    def filter(self, *args, **kwargs):
        pk = None
        for val in ('pk', 'pk__exact', 'id', 'id__exact'):
            if val in kwargs:
                pk = kwargs[val]
                break
        if pk is not None:
            opts = self.model._meta
            key = '%s.%s:%s' % (opts.app_label, opts.model_name, pk)
            obj = cache.get(key)
            if obj is not None:
                self._result_cache = [obj]
        return super(CacheQuerySet, self).filter(*args, **kwargs)


class CacheManager(models.Manager):
    def get_queryset(self):
        return CacheQuerySet(self.model)


def get_cache(key, default_value=None):
    return cache.get(key, default_value)


def delete_cache(key):
    return cache.delete(key)


def set_cache(key, value, timeout=None):
    cache.set(key, value, timeout=timeout)
