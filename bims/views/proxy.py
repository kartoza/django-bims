import sys
import urllib.parse
from django.http import HttpResponse
from django.views.decorators.csrf import requires_csrf_token
import requests


@requires_csrf_token
def proxy_request(request, path):
    if sys.version_info > (3, 0):
        get_keys = request.GET.keys()
    else:
        get_keys = request.GET.iterkeys()

    parameters = []
    for key in get_keys:
        value_list = request.GET.getlist(key)
        parameters.extend(['%s=%s' % (
            key, urllib.parse.quote(val)) for val in value_list])

    if parameters:
        path += '?' + '&'.join(parameters)

    if len(path.split('://')) == 1:
        new_path = path.split(':/')
        path = '://'.join(new_path)

    access_token = request.session.get('access_token', None)

    headers = {}
    if access_token is not None:
        headers['Access-Token'] = access_token

    try:
        response = requests.get(path, headers=headers, timeout=5)
    except requests.exceptions.Timeout:
        return HttpResponse("The request timed out.")
    except requests.exceptions.RequestException as e:
        return HttpResponse(f"An error occurred: {e}")

    return HttpResponse(
        response.content,
        status=response.status_code,
        content_type=response.headers['content-type']
    )
