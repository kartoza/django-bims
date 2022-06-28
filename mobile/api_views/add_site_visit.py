from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.views.collections_form import add_survey_occurrences


class AddSiteVisit(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """
        post_data = {
            'date': '2022-12-30',
            'owner_id': self.user.id,
            'site-id': location_site.id,
            'taxa-id-list': 'taxa_id_1,taxa_id_2',
            '{taxa_id_1}-observed': 'True',
            '{taxa_id_1}-abundance': '10',
            'abundance_type': 'number',
            'record_type': 'mobile',
            'biotope': biotope.id,
            'specific_biotope': specific_biotope.id,
            'substratum': substratum.id,
            'sampling_method': sampling_method.id
        }
        """
        try:
            collection_record_ids = add_survey_occurrences(self, request)
        except TypeError:
            raise Http404()
        return Response(
            collection_record_ids
        )
