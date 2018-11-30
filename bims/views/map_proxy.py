from proxy.views import proxy_view
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def proxy_request(request, path):
    extra_requests_arts = {}
    return proxy_view(request, path, extra_requests_arts)
