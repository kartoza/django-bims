import requests
from django.views import View
from django.http import JsonResponse

from bims.utils.taxonworks_client import TaxonWorksClient


class TaxonNamesView(View):
    """
    A Django Class-Based View to fetch Taxon Names from an external API.
    """
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests. Optionally accept `max_page` as a query parameter.
        """
        client = TaxonWorksClient()
        max_page = request.GET.get('max_page', 5)
        taxon_names = client.fetch_taxon_names(max_page=int(max_page))
        return JsonResponse(taxon_names, safe=False)
