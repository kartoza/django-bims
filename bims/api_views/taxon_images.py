# coding=utf-8
from django.conf import Settings
from rest_framework.views import APIView
from django.http import Http404
from rest_framework.response import Response
from bims.models import TaxonImage


class TaxonImageList(APIView):
    """Return list of taxon image"""

    def get(self, request, taxon):
        taxon_image_list = []
        taxon_images = TaxonImage.objects.filter(
                taxonomy=taxon
        )

        for image in taxon_images:
            taxon_image_list.append({
                'url': image.taxon_image.url
            })
        return Response(taxon_image_list)
