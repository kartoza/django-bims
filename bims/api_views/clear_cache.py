from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from bims.api_views.merge_sites import IsSuperUser
from bims.models.search_process import SearchProcess


class ClearCacheView(APIView):
    permission_classes = (IsSuperUser,)

    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            cache.clear()
            SearchProcess.objects.filter(
                finished=True,
                locked=False
            ).delete()
            return Response(
                {"message": "Cache cleared successfully."},
                status=HTTP_200_OK)
        return Response(
            {"error": "Permission denied."},
            status=HTTP_403_FORBIDDEN)
