from django.db import models
from django.conf import settings
from bims.models.taxonomy import Taxonomy
from bims.models.taxon_group_taxonomy import TaxonGroupTaxonomy


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

    reviewers = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        blank=True,
        through='TaxonomyUpdateReviewer'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'taxonomy_update_proposal'

    def reject_data(self, reviewer: settings.AUTH_USER_MODEL, comments: str = ''):
        if self.status == 'pending':
            self.status = 'rejected'
            TaxonomyUpdateReviewer.objects.update_or_create(
                taxonomy_update_proposal=self,
                reviewer=reviewer,
                status='rejected',
                comments=comments
            )
            self.save()
            TaxonGroupTaxonomy.objects.filter(
                taxongroup=self.taxon_group,
                taxonomy=self.original_taxonomy,
            ).update(
                is_validated=False,
                is_rejected=True
            )

    def approve(self, reviewer: settings.AUTH_USER_MODEL):
        """
        Apply the proposed changes to the associated Taxonomy instance
        and update its status to 'approved'.
        """
        TaxonomyUpdateReviewer.objects.update_or_create(
            taxonomy_update_proposal=self,
            reviewer=reviewer,
            status='approved'
        )
        top_level_taxon_group = self.taxon_group.get_top_level_parent()

        # Only top level experts can approve data
        if top_level_taxon_group.experts.filter(
            id=reviewer.id
        ).exists() or reviewer.is_superuser:
            fields_to_update = [
                'scientific_name',
                'canonical_name',
                'legacy_canonical_name',
                'rank',
                'taxonomic_status',
                'parent']
            for field in fields_to_update:
                setattr(
                    self.original_taxonomy,
                    field, getattr(self, field))
            self.original_taxonomy.save()
            self.status = 'approved'
            self.save()

            TaxonGroupTaxonomy.objects.filter(
                taxongroup=self.taxon_group,
                taxonomy=self.original_taxonomy,
            ).update(
                is_validated=True
            )


class TaxonomyUpdateReviewer(models.Model):
    taxonomy_update_proposal = models.ForeignKey(
        TaxonomyUpdateProposal,
        on_delete=models.CASCADE,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
