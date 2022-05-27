from django.http.response import Http404
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models import Biotope, TaxonGroup
from bims.models.sampling_method import SamplingMethod


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

        return Response({
            'broad_biotope': Biotope.objects.broad_biotope_list(
                taxon_group),
            'specific_biotope': Biotope.objects.specific_biotope_list(
                taxon_group),
            'substratum_biotope': Biotope.objects.substratum_list(
                taxon_group
            ),
            'sampling_method': SamplingMethod.objects.sampling_method_list(
                taxon_group
            )
        })
