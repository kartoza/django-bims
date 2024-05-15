import json
from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse
import hashlib

from bims.utils.domain import get_current_domain
import pdb


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


def cache_page_with_tag(timeout, tag, key_param=None):
    def decorator(func):
        @wraps(func)
        def _wrapped_view(request, *args, **kwargs):

            tag_key = f"response_tag:{tag}:{get_current_domain()}"
            if key_param:
                key_name = request.data.get(key_param)
                if not key_name:
                    return HttpResponse(
                        json.dumps({"error": "Key name is required"}),
                        content_type="application/json",
                        status=400
                    )
                tag_key += f':{key_name.replace(" ", "_")}'

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
