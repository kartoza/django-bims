from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


class TaxonGroupTaxonomy(models.Model):
    taxongroup = models.ForeignKey(
        'bims.TaxonGroup',
        on_delete=models.CASCADE,
    )

    taxonomy = models.ForeignKey(
        'bims.Taxonomy',
        on_delete=models.CASCADE,
    )

    is_validated = models.BooleanField(
        default=False,
        db_index=True
    )

    is_rejected = models.BooleanField(
        default=False,
        db_index=True
    )

    endemism = models.ForeignKey(
        'bims.Endemism',
        models.SET_NULL,
        verbose_name='Endemism',
        null=True,
        blank=True
    )

    origin = models.ForeignKey(
        'bims.TaxonOrigin',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text='Origin'
    )

    upstream_taxon_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        db_index=True,
        help_text=(
            'ID of the corresponding taxon on the upstream BIMS instance. '
            'Set during harvest; used to match taxa on re-harvest without '
            'relying solely on gbif_key or canonical name.'
        ),
    )

    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            'Timestamp of the last successful harvest that touched this membership. '
            'Null means the record was never harvested (created manually or via upload).'
        ),
    )

    upstream_checksum = models.CharField(
        max_length=64,
        blank=True,
        default='',
        help_text=(
            'SHA-256 hex digest of the canonical upstream taxon payload at the time '
            'of last harvest. If the checksum matches on re-harvest the record is '
            'skipped, avoiding unnecessary DB writes. An empty string means no '
            'checksum has been recorded yet.'
        ),
    )

    class Meta:
        unique_together = ('taxongroup', 'taxonomy')


@receiver([post_save, post_delete], sender=TaxonGroupTaxonomy)
def taxon_group_taxonomy_changed(sender, **kwargs):
    # Taxa of a group changed, so the landing page summary is outdated
    from bims.tasks.module_summary import queue_module_summary_refresh
    queue_module_summary_refresh()
