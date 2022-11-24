import base64

from django.core.files.base import ContentFile
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
            'sampling_method': sampling_method.id,
            'source_reference_id': source_reference.id
        }
        """
        try:
            post_data = request.data
            site_image_str = post_data.get('site_image', '')
            site_image = None
            if site_image_str:
                site_image_name = (
                    f'{post_data["date"]}_{request.user.id}_'
                    f'site_image_mobile.jpeg'
                )
                site_image = ContentFile(
                    base64.b64decode(site_image_str), name=site_image_name)
            survey = add_survey_occurrences(self, post_data, site_image)
            survey.mobile = True
            survey.save()
        except TypeError:
            raise Http404()
        return Response(
            {
                'survey_id': survey.id
            }
        )
