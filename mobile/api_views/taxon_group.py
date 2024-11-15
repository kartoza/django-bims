from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.api_views.taxon_update import is_expert
from bims.models.taxon_group import TaxonGroup
from bims.serializers.taxon_serializer import TaxonGroupSerializer
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory


class TaxonGroupList(APIView):
    """View to return list of taxon group"""
    def get(self, request, *args, **kwargs):
        taxon_group = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        )
        return Response(TaxonGroupSerializer(
            taxon_group, many=True
        ).data)


class TaxonGroupTotalValidated(APIView):
    """
    API View to retrieve total counts of validated and unvalidated taxonomies
    within a specified taxon group, including its children.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validated_count = 0
        self.unvalidated_count = 0

    def collect_taxonomy_ids(self, taxon_group):
        """
        Recursively collects counts of validated and unvalidated taxonomies
        within the given taxon group and its children.

        Args:
            taxon_group (TaxonGroup): The taxon group to collect counts from.
        """
        validated = taxon_group.taxonomies.filter(
            taxongrouptaxonomy__is_validated=True
        ).count()
        is_user_expert = is_expert(
            self.request.user,
            TaxonGroup.objects.get(id=taxon_group.id)
        )
        if self.request.user.is_superuser or is_user_expert:
            unvalidated = taxon_group.taxonomies.filter(
                taxongrouptaxonomy__is_validated=False
            ).count()
        else:
            unvalidated = 0

        self.validated_count += validated
        self.unvalidated_count += unvalidated

        children = TaxonGroup.objects.filter(parent=taxon_group)
        for child in children:
            self.collect_taxonomy_ids(child)

    def get(self, request, *args, **kwargs):
        """
        Handles GET request to retrieve the total counts of validated and unvalidated
        taxonomies for a specified taxon group.
        Returns:
            Response: A response containing the total counts of validated and unvalidated taxonomies.
        """
        taxon_group_id = kwargs.get('id')
        taxon_group = get_object_or_404(TaxonGroup, id=taxon_group_id)
        self.collect_taxonomy_ids(taxon_group)
        return Response({
            'total_validated': self.validated_count,
            'total_unvalidated': self.unvalidated_count
        })
