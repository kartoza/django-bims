import sys
from django.views.decorators.csrf import requires_csrf_token
from geonode.proxy.views import proxy


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
        parameters.extend(['%s=%s' % (key, val) for val in value_list])

    if parameters:
        path += '?' + '&'.join(parameters)

    # If somehow we get malformed url
    if len(path.split('://')) == 1:
        new_path = path.split(':/')
        path = '://'.join(new_path)

    return proxy(request, url=path)
