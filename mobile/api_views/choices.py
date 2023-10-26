from django.http.response import Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models import Biotope, TaxonGroup
from bims.models.sampling_method import SamplingMethod
from bims.models.hydroperiod import Hydroperiod
from bims.models.sampling_effort_measure import (
    SamplingEffortMeasure
)


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

        hydroperiod_choices = list(
            Hydroperiod.objects.all().values_list('name', flat=True)
        )

        sampling_effort_measure = list(SamplingEffortMeasure.objects.filter(
            Q(specific_module__isnull=True) |
            Q(specific_module_id=taxon_group.id)
        ).exclude(name='').values(
            'id', 'name'
        ))

        return Response({
            'broad_biotope': Biotope.objects.broad_biotope_list(
                taxon_group),
            'specific_biotope': Biotope.objects.specific_biotope_list(
                taxon_group),
            'substratum_biotope': Biotope.objects.substratum_list(
                taxon_group
            ),
            'sampling_method': sampling_method_list,
            'sampling_effort_measure': sampling_effort_measure,
            'hydroperiod': [{
                'id': hydroperiod,
                'name': hydroperiod
            } for hydroperiod in hydroperiod_choices]
        })
