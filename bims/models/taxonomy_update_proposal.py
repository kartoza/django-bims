from django.db import models
from django.conf import settings
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from bims.models.taxonomy import Taxonomy, AbstractTaxonomy, CustomTaggedTaxonomy, TaxonTag
from bims.models.taxon_group_taxonomy import TaxonGroupTaxonomy


class CustomTaggedUpdateTaxonomy(TaggedItemBase):
    content_object = models.ForeignKey(
        'TaxonomyUpdateProposal',
        on_delete=models.CASCADE)
    tag = models.ForeignKey(
        TaxonTag,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_items",
    )

    class Meta:
        verbose_name = "Custom Tagged Taxonomy"
        verbose_name_plural = "Custom Tagged Taxa"


class TaxonomyUpdateProposal(AbstractTaxonomy):
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

    tags = TaggableManager(
        blank=True,
        related_name='taxonomy_proposal_tags'
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='taxonomy_proposal_owner'
    )

    biographic_distributions = TaggableManager(
        through=CustomTaggedUpdateTaxonomy,
        related_name='taxonomy_proposal_bio_distribution',
        blank=True,
    )

    vernacular_names = models.ManyToManyField(
        to='VernacularName',
        related_name='%(class)s_vernacular_names',
        blank=True,
    )

    parent = models.ForeignKey(
        verbose_name='Parent',
        to='bims.Taxonomy',
        on_delete=models.SET_NULL,
        related_name='%(class)s_parent',
        null=True,
        blank=True
    )

    national_conservation_status = models.ForeignKey(
        'IUCNStatus',
        models.SET_NULL,
        related_name='%(class)s_national_conservation_status',
        verbose_name='National Conservation Status',
        null=True,
        blank=True,
    )

    iucn_status = models.ForeignKey(
        'IUCNStatus',
        models.SET_NULL,
        related_name='%(class)s_iucn_status',
        verbose_name='Global Red List Status (IUCN)',
        null=True,
        blank=True,
    )

    endemism = models.ForeignKey(
        'Endemism',
        models.SET_NULL,
        related_name='%(class)s_endemism',
        verbose_name='Endemism',
        null=True,
        blank=True
    )

    accepted_taxonomy = models.ForeignKey(
        related_name='taxonomy_update_proposal_accepted_taxonomy',
        to='bims.Taxonomy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
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

    # Reference to the taxon group currently under review or validation.
    # This may change based on the proposal's review process.
    taxon_group_under_review = models.ForeignKey(
        'bims.TaxonGroup',
        related_name='taxon_group_under_review',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Taxon Group Under Review"
    )

    reviewers = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        blank=True,
        through='TaxonomyUpdateReviewer',
        related_name='taxonomy_update_proposals_reviewers',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bims_taxonomy_update_proposal'
        # unique_together = ('original_taxonomy', 'taxon_group', 'status')

    def reject_data(self, reviewer: settings.AUTH_USER_MODEL, comments: str = ''):
        if self.status == 'pending':
            self.status = 'rejected'
            TaxonomyUpdateReviewer.objects.update_or_create(
                taxonomy_update_proposal=self,
                reviewer=reviewer,
                defaults={
                    'status': 'rejected',
                    'comments': comments
                }
            )
            self.save()
            TaxonGroupTaxonomy.objects.filter(
                taxongroup=self.taxon_group,
                taxonomy=self.original_taxonomy,
            ).update(
                is_validated=True
            )

    def validate_taxon(self, taxon_group, taxonomy):
        TaxonGroupTaxonomy.objects.filter(
            taxongroup=taxon_group,
            taxonomy=taxonomy,
        ).update(
            is_validated=True
        )
        if taxon_group.parent:
            self.validate_taxon(taxon_group.parent, taxonomy)

    def approve(self, reviewer: settings.AUTH_USER_MODEL):
        """
        Apply the proposed changes to the associated Taxonomy instance
        and update its status to 'approved'.
        """
        TaxonomyUpdateReviewer.objects.update_or_create(
            taxonomy_update_proposal=self,
            reviewer=reviewer,
            defaults={
                'status': 'approved'
            }
        )
        top_level_taxon_group = self.taxon_group.get_top_level_parent()

        if self.taxon_group_under_review:
            self.taxon_group_under_review = top_level_taxon_group
            self.save()

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
                'endemism',
                'iucn_status',
                'accepted_taxonomy',
                'parent',
                'tags',
                'origin']
            for field in fields_to_update:
                if field == 'tags':
                    self.original_taxonomy.tags.set(getattr(self, field).all())
                else:
                    setattr(
                        self.original_taxonomy,
                        field, getattr(self, field))
            self.original_taxonomy.save()
            self.status = 'approved'
            self.save()

            self.validate_taxon(
                self.taxon_group,
                self.original_taxonomy
            )
            return


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
