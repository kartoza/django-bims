import sys
import urllib.parse
from django.views.decorators.csrf import requires_csrf_token
from proxy.views import proxy_view


@requires_csrf_token
def proxy_request(request, path):
    if sys.version_info > (3, 0):
        # Python 3 code in this block
        get_keys = request.GET.keys()
    else:
        # Python 2 code in this block
        get_keys = request.GET.iterkeys()

    parameters = []
    for key in get_keys:
        value_list = request.GET.getlist(key)
        if key == 'viewparams':
            parameters.extend(['%s=%s' % (
                key, urllib.parse.quote(val)) for val in value_list])
        else:
            parameters.extend(
                ['%s=%s' % (
                    key, urllib.parse.quote(val)) for val in value_list])

    if parameters:
        path += '?' + '&'.join(parameters)

    # If somehow we get malformed url
    if len(path.split('://')) == 1:
        new_path = path.split(':/')
        path = '://'.join(new_path)

    request.session['access_token'] = None
    return proxy_view(request, url=path)
