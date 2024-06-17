from braces.views import LoginRequiredMixin
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers

from bims.utils.cites import CitesSpeciesPlusAPI
from bims.utils.cache import cache_page_with_tag


class TaxonNameSerializer(serializers.Serializer):
    taxon_name = serializers.CharField(max_length=100)


CITES_CACHE_KEY = 'CITES_API_CACHE'

def get_cites_listing_data(taxon_name: str):
    cites_api = CitesSpeciesPlusAPI()
    taxon_concepts_response = cites_api.list_taxon_concepts(
        params={'name': taxon_name})
    taxon_concepts = taxon_concepts_response.get('taxon_concepts', [])

    if not taxon_concepts:
        return False, {"error": "No data found for this species."}

    # Call the list_taxon_concepts API to get the taxon concept ID
    taxon_concept_id = taxon_concepts[0].get('id')
    taxon_concept = taxon_concepts[0]

    if not taxon_concept_id:
        return False, {"error": "Taxon concept ID not found."}

    # Get CITES legislation for the taxon concept ID
    cites_legislation = cites_api.get_cites_legislation(taxon_concept_id)

    # Extract CITES listing information
    cites_listings = taxon_concept.get('cites_listings', [])

    if len(cites_listings) == 0:
        return False, {"error": "No CITES listing found for this species."}

    cites_listing_info = [
        {
            'appendix': listing.get('appendix'),
            'annotation': listing.get('annotation'),
            'effective_at': listing.get('effective_at')
        }
        for listing in cites_listings
    ]
    cites_data = {
        'taxon_concept_id': taxon_concept_id,
        'taxon_name': taxon_concept.get('full_name'),
        'cites_listing': taxon_concept.get('cites_listing'),
        'cites_legislation': cites_legislation,
        'cites_listing_info': cites_listing_info
    }
    return True, cites_data


class TaxaCitesStatusAPIView(LoginRequiredMixin, APIView):

    @method_decorator(
        cache_page_with_tag(60 * 60 * 24, CITES_CACHE_KEY, key_param='taxon_name'),
        name='dispatch')
    def post(self, request):
        serializer = TaxonNameSerializer(data=request.data)
        if serializer.is_valid():
            taxon_name = serializer.validated_data['taxon_name']
            success, response_data = get_cites_listing_data(taxon_name)
            if not success:
                return Response(response_data,
                                status=status.HTTP_404_NOT_FOUND)
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
