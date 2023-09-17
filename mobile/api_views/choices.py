from django.http.response import Http404
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models import Biotope, TaxonGroup
from bims.models.sampling_method import SamplingMethod
from bims.enums.ecosystem_type import HYDROPERIOD_CHOICES


class AllChoicesApi(APIView):
    """
    Get all choices for collection record form, e.g. Biotope, Sampling Method
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args):
        module = request.GET.get('module', None)
        if not module:
            raise Http404()

        taxon_group = get_object_or_404(
            TaxonGroup,
            id=module
        )
        sampling_methods = SamplingMethod.objects.sampling_method_list(
            taxon_group
        )
        sampling_method_list = []
        for sampling_method in sampling_methods:
            sampling_method_list.append({
                'id': sampling_method['id'],
                'name': sampling_method['sampling_method']
            })

        return Response({
            'broad_biotope': Biotope.objects.broad_biotope_list(
                taxon_group),
            'specific_biotope': Biotope.objects.specific_biotope_list(
                taxon_group),
            'substratum_biotope': Biotope.objects.substratum_list(
                taxon_group
            ),
            'sampling_method': sampling_method_list,
            'hydroperiod': [{
                'id': hydroperiod[0],
                'name': hydroperiod[1]
            } for hydroperiod in HYDROPERIOD_CHOICES]
        })
