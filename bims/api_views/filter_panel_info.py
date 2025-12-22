from rest_framework.response import Response

from bims.models.filter_panel_info import FilterPanelInfo
from bims.utils.api_view import BimsApiView


class FilterPanelInfoView(BimsApiView):
    """Returns active filter panel descriptions used by the search panel."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        descriptions = FilterPanelInfo.objects.filter(
            is_active=True,
            description__isnull=False
        ).exclude(
            description__exact=''
        ).order_by('title').values('title', 'description')
        return Response(list(descriptions))
