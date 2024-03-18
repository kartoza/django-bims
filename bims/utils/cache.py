import json
from functools import wraps

from django.contrib.sites.models import Site
from django.core.cache import cache
from django.http import HttpResponse
import hashlib


def cache_with_tag(key, value, tag, timeout=None):
    cache.set(key, value, timeout=timeout)
    tag_key = f"tag:{tag}"
    existing_keys = cache.get(tag_key, set())
    existing_keys.add(key)
    cache.set(tag_key, existing_keys, timeout=timeout)


def clear_cache_by_tag(tag):
    tag_key = f"tag:{tag}"
    keys_to_clear = cache.get(tag_key, set())
    for key in keys_to_clear:
        cache.delete(key)
    cache.delete(tag_key)


def cache_page_with_tag(timeout, tag):
    def decorator(func):
        @wraps(func)
        def _wrapped_view(request, *args, **kwargs):
            cache_key = hashlib.sha256(request.get_full_path().encode('utf-8')).hexdigest()
            tag_key = f"response_tag:{tag}:{cache_key}:{Site.objects.get_current().id}"

            cached_response = cache.get(tag_key)
            if cached_response:
                return HttpResponse(
                    json.dumps(cached_response),
                    content_type="application/json")

            response = func(request, *args, **kwargs)

            cache_with_tag(tag_key, response.data, tag, timeout=timeout)

            return response
        return _wrapped_view
    return decorator
