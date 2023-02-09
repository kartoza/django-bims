import base64

from bims.models.chemical_record import ChemicalRecord

from bims.models.survey import Survey
from django.core.files.base import ContentFile
from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.views.collections_form import add_survey_occurrences


def process_abiotic_data(survey: Survey, abiotic: dict):
    """
    Record abiotic data
    :param survey: Survey object for this abiotic data
    :param abiotic: [
        {
            'id': '{chem_id}',
            'value': '{abiotic_value}'
        }
        ...
    ]
    """
    for abiotic_data in abiotic:
        chem_record, _ = ChemicalRecord.objects.get_or_create(
            date=survey.date,
            chem_id=abiotic_data['id'],
            location_site=survey.site,
            survey=survey,
            value=float(abiotic_data['value'])
        )


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
            'source_reference_id': source_reference.id,
            'abiotic': [
                {
                    'id': '{chem_id}',
                    'value': '{abiotic_value}'
                }
                ...
            ]
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

            process_abiotic_data(
                survey,
                post_data.get('abiotic', [])
            )

        except TypeError:
            raise Http404()
        return Response(
            {
                'survey_id': survey.id
            }
        )
