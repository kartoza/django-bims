from django.db import models
from bims.models.taxonomy import Taxonomy


class TaxonomyUpdateProposal(Taxonomy):
    # Status of the proposal (e.g., pending, approved, rejected)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )

    original_taxonomy = models.ForeignKey(
        Taxonomy,
        verbose_name='Original Taxonomy',
        on_delete=models.CASCADE,
        related_name='proposals',
        null=True,
    )

    taxon_group = models.ForeignKey(
        'bims.TaxonGroup',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'taxonomy_update_proposal'

    def approve(self):
        """
        Apply the proposed changes to the associated Taxonomy instance
        and update its status to 'approved'.
        """
        if self.status == 'pending':
            fields_to_update = [
                'scientific_name',
                'canonical_name',
                'legacy_canonical_name',
                'rank',
                'taxonomic_status',
                'parent']
            for field in fields_to_update:
                setattr(
                    self.original_taxonomy, field, getattr(self, field))
            self.original_taxonomy.save()
            self.status = 'approved'
            self.save()
