from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.api_views.taxon_update import is_expert
from bims.enums import TaxonomicStatus
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
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView


class TaxonGroupTotalValidated(APIView):
    """
    Return counts for a taxon group by:
      - accepted_validated
      - accepted_unvalidated
      - synonym_validated
      - synonym_unvalidated
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accepted_validated = 0
        self.accepted_unvalidated = 0
        self.synonym_validated = 0
        self.synonym_unvalidated = 0

    def _status_queries(self):
        accepted_names = {
            TaxonomicStatus.ACCEPTED.name,
            TaxonomicStatus.DOUBTFUL.name,
        }
        synonym_names = {
            TaxonomicStatus.SYNONYM.name,
            TaxonomicStatus.HETEROTYPIC_SYNONYM.name,
            TaxonomicStatus.HOMOTYPIC_SYNONYM.name,
            TaxonomicStatus.PROPARTE_SYNONYM.name,
            TaxonomicStatus.MISAPPLIED.name,
        }

        accepted_q = (
            Q(taxonomic_status__in=accepted_names) |
            Q(taxonomic_status__isnull=True) |
            Q(taxonomic_status="")
        )
        synonym_q = Q(taxonomic_status__in=synonym_names)

        return accepted_q, synonym_q

    def collect_taxonomy_ids(self, taxon_group):
        """
        Recursively aggregate counts for the given taxon group + children.
        """
        accepted_q, synonym_q = self._status_queries()

        is_user_expert = is_expert(self.request.user, get_object_or_404(TaxonGroup, id=taxon_group.id))
        can_view_unvalidated = self.request.user.is_superuser or is_user_expert

        qs = taxon_group.taxonomies.all()

        # Validated
        self.accepted_validated += qs.filter(
            accepted_q,
            taxongrouptaxonomy__is_validated=True
        ).count()

        self.synonym_validated += qs.filter(
            synonym_q,
            taxongrouptaxonomy__is_validated=True
        ).count()

        # Unvalidated (masked if no permission)
        if can_view_unvalidated:
            self.accepted_unvalidated += qs.filter(
                accepted_q,
                taxongrouptaxonomy__is_validated=False
            ).count()

            self.synonym_unvalidated += qs.filter(
                synonym_q,
                taxongrouptaxonomy__is_validated=False
            ).count()

        # Recurse into children
        for child in TaxonGroup.objects.filter(parent=taxon_group):
            self.collect_taxonomy_ids(child)

    def get(self, request, *args, **kwargs):
        """
        GET: return counts split by accepted/synonym and validated/unvalidated.
        Unvalidated counts are 0 for non-privileged users.
        """
        taxon_group_id = kwargs.get("id")
        taxon_group = get_object_or_404(TaxonGroup, id=taxon_group_id)

        self.collect_taxonomy_ids(taxon_group)

        is_user_expert = is_expert(request.user, taxon_group)
        can_view_unvalidated = request.user.is_superuser or is_user_expert
        accepted_unvalidated = self.accepted_unvalidated if can_view_unvalidated else 0
        synonym_unvalidated = self.synonym_unvalidated if can_view_unvalidated else 0

        total_validated = self.accepted_validated + self.synonym_validated
        total_unvalidated = accepted_unvalidated + synonym_unvalidated

        return Response({
            "accepted_validated": self.accepted_validated,
            "accepted_unvalidated": accepted_unvalidated,
            "synonym_validated": self.synonym_validated,
            "synonym_unvalidated": synonym_unvalidated,

            "total_validated": total_validated,
            "total_unvalidated": total_unvalidated,
        })
