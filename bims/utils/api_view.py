import ast
from rest_framework.views import APIView


class BimsApiView(APIView):

    def is_background_request(self, default=True):
        """Check whether the request wants to use a background process"""
        if self.request.GET.get('background', None):
            try:
                return ast.literal_eval(self.request.GET.get(
                    'background'
                ))
            except ValueError:
                return False
        return default

    def is_cached(self, default=True):
        """Check whether the request wants to use a cached data"""
        if self.request.GET.get('cached', None):
            try:
                return ast.literal_eval(self.request.GET.get(
                    'cached'
                ))
            except ValueError:
                return False
        return default
