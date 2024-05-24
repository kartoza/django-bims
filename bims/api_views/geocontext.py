from rest_framework.response import Response
from rest_framework.views import APIView
from braces.views import SuperuserRequiredMixin

from bims.cache import get_cache, HARVESTING_GEOCONTEXT, set_cache
from bims.tasks import update_location_context
from bims.utils.location_context import get_location_context_data


class IsHarvestingGeocontext(SuperuserRequiredMixin, APIView):
    """
    API view to check if the geocontext is currently being harvested.
    Only accessible to superusers.
    """
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to determine the harvesting status.

        :param request: HTTP request object
        :return: JSON response with harvesting status
        """
        try:
            is_harvesting = get_cache(HARVESTING_GEOCONTEXT, False)
            return Response({'harvesting': is_harvesting})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class HarvestGeocontextView(SuperuserRequiredMixin, APIView):

    def harvest_geocontext(self, is_all=False):
        update_location_context.delay(
            location_site_id=None,
            generate_site_code=False,
            generate_filter=True,
            only_empty=not is_all
        )

    def post(self, request, *args, **kwargs):
        is_harvesting = get_cache(HARVESTING_GEOCONTEXT, False)
        if is_harvesting:
            return Response({'error': 'Harvesting is already in progress.'}, status=400)

        # Set harvesting flag to true
        set_cache(HARVESTING_GEOCONTEXT, True)

        try:
            # check if harvesting all or just empty
            is_all = request.data.get('is_all', False)

            self.harvest_geocontext(is_all)

            return Response({'status': 'Harvesting started successfully.'}, status=200)
        except Exception as e:
            # Reset harvesting flag in case of exception
            set_cache(HARVESTING_GEOCONTEXT, False)
            return Response({'error': str(e)}, status=500)


class ClearHarvestingGeocontextCache(SuperuserRequiredMixin, APIView):
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to determine the harvesting status.

        :param request: HTTP request object
        :return: JSON response with harvesting status
        """
        set_cache(HARVESTING_GEOCONTEXT, False)
        try:
            is_harvesting = get_cache(HARVESTING_GEOCONTEXT, False)
            return Response({'harvesting': is_harvesting})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

