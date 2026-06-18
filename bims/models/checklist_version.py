# coding=utf-8
"""
ChecklistVersion and ChecklistSnapshot — versioned taxonomy publishing
in Catalogue of Life Data Package (ColDP) format.

Architecture
------------
ChecklistVersion
    One record per module (TaxonGroup) release.  Carries version string,
    DOI, status, and the approved-proposal changelog.

ChecklistSnapshot
    Pre-rendered, write-once table of ColDP NameUsage rows — one row per
    taxon per published version.
"""
import uuid as _uuid

from django.conf import settings
from django.db import models
from preferences import preferences


class ChecklistSnapshot(models.Model):
    """
    One pre-rendered checklist NameUsage row per taxon per ChecklistVersion.
    """

    CHANGE_ADDED     = 'added'
    CHANGE_UPDATED   = 'updated'
    CHANGE_UNCHANGED = 'unchanged'
    CHANGE_DELETED   = 'deleted'

    CHANGE_CHOICES = [
        (CHANGE_ADDED,     'Added'),
        (CHANGE_UPDATED,   'Updated'),
        (CHANGE_UNCHANGED, 'Unchanged'),
        (CHANGE_DELETED,   'Deleted'),
    ]

    checklist_version = models.ForeignKey(
        'ChecklistVersion',
        on_delete=models.CASCADE,
        related_name='snapshot_rows',
        db_column='checklist_version_id',
        db_index=True,
    )
    checklist_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text='Stable taxon identifier used in checklist (str of Taxonomy.pk).',
    )
    parent_checklist_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='checklist_id of the parent taxon.',
    )
    basionym_checklist_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='checklist_id of the accepted taxon for synonyms.',
    )
    rank = models.CharField(max_length=50, blank=True, default='')
    scientific_name = models.CharField(max_length=512, db_index=True)
    authorship = models.CharField(max_length=255, blank=True, default='')
    taxonomic_status = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text='accepted, synonym, ambiguous synonym, misapplied, etc.',
    )
    name_status = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text='establishmentMeans / name status from ColDP.',
    )

    kingdom  = models.CharField(max_length=200, blank=True, default='')
    phylum   = models.CharField(max_length=200, blank=True, default='')
    klass    = models.CharField(max_length=200, blank=True, default='',
                                db_column='class')
    order    = models.CharField(max_length=200, blank=True, default='')
    family   = models.CharField(max_length=200, blank=True, default='')
    subfamily    = models.CharField(max_length=200, blank=True, default='')
    tribe        = models.CharField(max_length=200, blank=True, default='')
    subtribe     = models.CharField(max_length=200, blank=True, default='')
    genus    = models.CharField(max_length=200, blank=True, default='')
    subgenus     = models.CharField(max_length=200, blank=True, default='')
    species      = models.CharField(max_length=200, blank=True, default='')
    subspecies   = models.CharField(max_length=200, blank=True, default='')
    variety      = models.CharField(max_length=200, blank=True, default='')
    species_group = models.CharField(max_length=200, blank=True, default='')

    canonical_name = models.CharField(max_length=512, blank=True, default='')
    accepted_taxon = models.CharField(
        max_length=512, blank=True, default='',
        help_text='Canonical name of accepted taxon (for synonyms).',
    )
    common_name  = models.CharField(max_length=512, blank=True, default='')
    fada_id      = models.CharField(max_length=255, blank=True, default='')
    cites_listing = models.CharField(max_length=255, blank=True, default='')

    origin       = models.CharField(max_length=100, blank=True, default='')
    endemism     = models.CharField(max_length=100, blank=True, default='')
    invasion     = models.CharField(max_length=100, blank=True, default='')

    conservation_status_global   = models.CharField(max_length=100, blank=True, default='')
    conservation_status_national = models.CharField(max_length=100, blank=True, default='')

    gbif_key = models.CharField(max_length=100, blank=True, default='')

    tags = models.JSONField(
        default=dict,
        help_text='Snapshot of {tag_name: "Y"/"?"} for tags and biographic distributions.',
    )
    additional_data = models.JSONField(
        default=dict, blank=True,
        help_text='Snapshot of extra taxon attributes {attr_name: value}.',
    )

    vernacular_names = models.JSONField(
        default=list,
        help_text='Snapshot of [{name, language}] at publish time.',
    )
    distributions = models.JSONField(
        default=list,
        help_text='Snapshot of [{area, status}] at publish time.',
    )
    reference_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='ColDP Reference.ID for the source reference.',
    )
    remarks = models.TextField(
        blank=True,
        default='',
        help_text='Free-text remarks field in ColDP NameUsage.',
    )

    change_type = models.CharField(
        max_length=10,
        choices=CHANGE_CHOICES,
        default=CHANGE_UNCHANGED,
        db_index=True,
        help_text='Whether this taxon was added, updated, unchanged, or deleted in this version.',
    )

    class Meta:
        unique_together     = [('checklist_version', 'checklist_id')]
        verbose_name        = 'Checklist Snapshot Row'
        verbose_name_plural = 'Checklist Snapshot Rows'
        indexes = [
            models.Index(fields=['checklist_id', 'checklist_version']),
        ]

    def __str__(self):
        version = self.__dict__.get('checklist_version')
        version_repr = version if version is not None else (
            self.checklist_version_id or 'deleted checklist version'
        )
        return f'{self.scientific_name} [{version_repr}]'


class ChecklistVersion(models.Model):

    STATUS_DRAFT     = 'draft'
    STATUS_PUBLISHED = 'published'

    STATUS_CHOICES = [
        (STATUS_DRAFT,     'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=_uuid.uuid4,
        editable=False,
        help_text=(
            'Stable UUID for this release. '
            'Embedded in generated PDFs and returned by the API.'
        ),
    )

    taxon_group = models.ForeignKey(
        'bims.TaxonGroup',
        on_delete=models.CASCADE,
        related_name='checklist_versions',
        db_column='taxon_group_id',
        help_text='The module (TaxonGroup) this version belongs to.',
    )

    checklist = models.ForeignKey(
        'bims.TaxonomyChecklist',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions',
        db_column='checklist_id',
        help_text='Optional parent dataset record (ColDP dataset-level metadata).',
    )

    version = models.CharField(
        max_length=50,
        help_text='Human-readable version string, e.g. "1.0", "2025.1".',
    )

    previous_version = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='next_versions',
        db_column='previous_version_id',
        help_text='Immediately preceding published version for this module.',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )

    doi = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='DOI assigned at publish time, e.g. https://doi.org/10.XXXX/YYYY.',
    )

    dataset_key = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='ChecklistBank / COL dataset key returned after upload.',
    )

    license = models.ForeignKey(
        'bims.Licence',
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )

    notes = models.TextField(
        blank=True,
        default='',
        help_text='Internal release notes visible to editors.',
    )

    taxa_count       = models.IntegerField(default=0)
    additions_count  = models.IntegerField(default=0)
    updates_count    = models.IntegerField(default=0)
    deletions_count  = models.IntegerField(default=0)
    is_publishing    = models.BooleanField(
        default=False,
        help_text='True while the publish task is running. Cleared when publishing completes or fails.',
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='checklist_versions_created',
        db_column='created_by_id',
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='checklist_versions_published',
        db_column='published_by_id',
    )

    created_at   = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    _DIFF_FIELDS = (
        'scientific_name', 'rank', 'authorship', 'taxonomic_status',
        'parent_checklist_id', 'basionym_checklist_id',
        'kingdom', 'phylum', 'klass', 'order', 'family',
        'subfamily', 'tribe', 'subtribe', 'genus', 'subgenus',
        'species', 'subspecies', 'variety', 'species_group',
        'canonical_name', 'accepted_taxon', 'common_name',
        'origin', 'endemism', 'invasion',
        'conservation_status_global', 'conservation_status_national',
        'gbif_key', 'fada_id', 'cites_listing',
        'vernacular_names', 'distributions', 'reference_id',
    )

    def publish(self, published_by=None):
        """
        Transition this version to published status.
        """
        from django.utils import timezone
        from bims.models.taxonomy import Taxonomy

        if self.status == self.STATUS_PUBLISHED:
            return

        # Mark as publishing so the UI can show a spinner even across page refreshes
        self.is_publishing = True
        self.save(update_fields=['is_publishing'])

        # Collect all descendant taxon group IDs
        descendant_groups = self.taxon_group.get_all_children()
        taxon_group_ids = [self.taxon_group_id]
        taxon_group_ids.extend(group.id for group in descendant_groups)

        # Build a lookup of previous snapshot rows keyed by checklist_id
        prev_snapshot = {}
        if self.previous_version_id:
            prev_snapshot = {
                row['checklist_id']: row
                for row in ChecklistSnapshot.objects.filter(
                    checklist_version_id=self.previous_version_id
                ).values('checklist_id', *self._DIFF_FIELDS)
            }

        rows = []
        additions = 0
        updates = 0
        current_ids = set()

        for taxonomy in (
            Taxonomy.objects.filter(
                taxongrouptaxonomy__taxongroup_id__in=taxon_group_ids,
                taxongrouptaxonomy__is_validated=True,
            )
            .distinct()
            .select_related(
                'parent', 'accepted_taxonomy', 'source_reference',
                'origin', 'endemism', 'iucn_status', 'national_conservation_status',
                'invasion', 'species_group',
            )
            .prefetch_related('vernacular_names', 'biographic_distributions', 'tags')
        ):
            row = self.build_snapshot_row(taxonomy, ChecklistSnapshot.CHANGE_UNCHANGED)
            cid = row.checklist_id
            current_ids.add(cid)

            if cid not in prev_snapshot:
                row.change_type = ChecklistSnapshot.CHANGE_ADDED
                additions += 1
            else:
                prev = prev_snapshot[cid]
                changed = any(
                    getattr(row, field) != prev[field]
                    for field in self._DIFF_FIELDS
                )
                if changed:
                    row.change_type = ChecklistSnapshot.CHANGE_UPDATED
                    updates += 1

            rows.append(row)

        deleted_ids = set(prev_snapshot.keys()) - current_ids
        deletions = len(deleted_ids)
        for cid in deleted_ids:
            prev = prev_snapshot[cid]
            rows.append(ChecklistSnapshot(
                checklist_version=self,
                checklist_id=cid,
                scientific_name=prev['scientific_name'],
                rank=prev['rank'],
                authorship=prev.get('authorship', ''),
                taxonomic_status=prev.get('taxonomic_status', ''),
                parent_checklist_id=prev.get('parent_checklist_id', ''),
                basionym_checklist_id=prev.get('basionym_checklist_id', ''),
                kingdom=prev.get('kingdom', ''),
                phylum=prev.get('phylum', ''),
                klass=prev.get('klass', ''),
                order=prev.get('order', ''),
                family=prev.get('family', ''),
                subfamily=prev.get('subfamily', ''),
                tribe=prev.get('tribe', ''),
                subtribe=prev.get('subtribe', ''),
                genus=prev.get('genus', ''),
                subgenus=prev.get('subgenus', ''),
                species=prev.get('species', ''),
                subspecies=prev.get('subspecies', ''),
                variety=prev.get('variety', ''),
                species_group=prev.get('species_group', ''),
                canonical_name=prev.get('canonical_name', ''),
                accepted_taxon=prev.get('accepted_taxon', ''),
                common_name=prev.get('common_name', ''),
                origin=prev.get('origin', ''),
                endemism=prev.get('endemism', ''),
                invasion=prev.get('invasion', ''),
                conservation_status_global=prev.get('conservation_status_global', ''),
                conservation_status_national=prev.get('conservation_status_national', ''),
                gbif_key=prev.get('gbif_key', ''),
                fada_id=prev.get('fada_id', ''),
                cites_listing=prev.get('cites_listing', ''),
                vernacular_names=prev.get('vernacular_names', []),
                distributions=prev.get('distributions', []),
                reference_id=prev.get('reference_id', ''),
                change_type=ChecklistSnapshot.CHANGE_DELETED,
            ))

        ChecklistSnapshot.objects.bulk_create(rows, ignore_conflicts=True)

        self.taxa_count      = len(current_ids)
        self.additions_count = additions
        self.updates_count   = updates
        self.deletions_count = deletions
        self.is_publishing   = False
        self.status          = self.STATUS_PUBLISHED
        self.published_at    = timezone.now()
        self.published_by    = published_by
        self.save(update_fields=[
            'status', 'published_at', 'published_by',
            'taxa_count', 'additions_count', 'updates_count', 'deletions_count',
            'is_publishing',
        ])

    @staticmethod
    def _fada_taxon_id(obj) -> str:
        """Return fada:{fada_id} when available, else {site_prefix}:{pk}."""
        if obj and getattr(obj, 'fada_id', None):
            return f'fada:{obj.fada_id}'
        if not obj:
            return ''
        prefix = (
            getattr(preferences.SiteSetting, 'default_data_source', '') or ''
        ).lower()
        return f'{prefix}:{obj.pk}' if prefix else str(obj.pk)

    @staticmethod
    def _iucn_display(status_obj):
        from bims.models.iucn_status import IUCNStatus
        if not status_obj:
            return 'Not evaluated'
        for code, label in IUCNStatus.CATEGORY_CHOICES:
            if code == status_obj.category:
                return label
        return 'Not evaluated'

    @staticmethod
    def _species_epithet(taxonomy):
        name = taxonomy.species_name or ''
        genus = taxonomy.genus_name or ''
        if genus and name.startswith(genus):
            name = name[len(genus):].strip()
        return name

    @staticmethod
    def _subspecies_epithet(taxonomy):
        name = taxonomy.sub_species_name or ''
        genus = taxonomy.genus_name or ''
        if genus:
            name = name.replace(genus, '', 1).strip()
        species = ChecklistVersion._species_epithet(taxonomy)
        if species:
            name = name.replace(species, '', 1).strip()
        return name

    def build_snapshot_row(self, taxonomy, change_type):
        """
        Construct a ChecklistSnapshot instance (not yet saved) from a
        Taxonomy object.  All lookups happen here so export is a plain
        table dump later.
        """
        vernacular_names = [
            {'name': v.name, 'language': v.language}
            for v in taxonomy.vernacular_names.all()
        ]
        distributions = [
            {'area': tag.name}
            for tag in taxonomy.biographic_distributions.all()
        ]

        common_name = next(
            (v['name'] for v in vernacular_names
             if (v.get('language') or '').lower().startswith('en')),
            '',
        )

        tag_dict = {}
        for tag in list(taxonomy.tags.all()) + list(taxonomy.biographic_distributions.all()):
            name = tag.name.strip()
            value = '?' if '(?)' in name else 'Y'
            tag_dict[name.replace('(?)', '').strip()] = value

        variety = ''
        if taxonomy.rank != 'SUBSPECIES':
            variety = taxonomy.variety_name or ''

        subspecies = ''
        if taxonomy.rank != 'VARIETY':
            subspecies = self._subspecies_epithet(taxonomy)

        return ChecklistSnapshot(
            checklist_version=self,
            checklist_id=self._fada_taxon_id(taxonomy),
            parent_checklist_id=(
                self._fada_taxon_id(taxonomy.parent) if taxonomy.parent_id else ''
            ),
            basionym_checklist_id=(
                self._fada_taxon_id(taxonomy.accepted_taxonomy)
                if taxonomy.accepted_taxonomy_id else ''
            ),
            rank=taxonomy.rank or '',
            scientific_name=taxonomy.scientific_name or '',
            canonical_name=taxonomy.canonical_name or '',
            authorship=taxonomy.author or '',
            taxonomic_status=taxonomy.taxonomic_status or '',
            accepted_taxon=(
                taxonomy.accepted_taxonomy.canonical_name
                if taxonomy.accepted_taxonomy_id else ''
            ),
            common_name=common_name,
            kingdom=taxonomy.kingdom_name,
            phylum=taxonomy.phylum_name,
            klass=taxonomy.class_name,
            order=taxonomy.order_name,
            family=taxonomy.family_name,
            subfamily=taxonomy.sub_family_name or '',
            tribe=taxonomy.tribe_name or '',
            subtribe=taxonomy.sub_tribe_name or '',
            genus=taxonomy.genus_name,
            subgenus=taxonomy.sub_genus_name or '',
            species=self._species_epithet(taxonomy),
            subspecies=subspecies,
            variety=variety,
            species_group=(
                taxonomy.species_group.name if taxonomy.species_group else ''
            ),
            origin=taxonomy.origin.category if taxonomy.origin else 'Unknown',
            endemism=taxonomy.endemism.name if taxonomy.endemism else 'Unknown',
            invasion=(taxonomy.invasion.category or '') if taxonomy.invasion else '',
            conservation_status_global=self._iucn_display(taxonomy.iucn_status),
            conservation_status_national=(
                self._iucn_display(taxonomy.national_conservation_status)
                if taxonomy.national_conservation_status else ''
            ),
            gbif_key=str(taxonomy.gbif_key) if taxonomy.gbif_key else '',
            fada_id=str(taxonomy.fada_id) if taxonomy.fada_id else '',
            cites_listing=taxonomy.cites_listing or '',
            additional_data=taxonomy.additional_data or {},
            tags=tag_dict,
            vernacular_names=vernacular_names,
            distributions=distributions,
            reference_id=(
                str(taxonomy.source_reference_id)
                if taxonomy.source_reference_id else ''
            ),
            change_type=change_type,
        )

    @property
    def changelog_summary(self):
        return {
            'additions': self.additions_count,
            'updates':   self.updates_count,
            'deletions': self.deletions_count,
            'total':     self.additions_count + self.updates_count + self.deletions_count,
        }

    class Meta:
        verbose_name        = 'Checklist Version'
        verbose_name_plural = 'Checklist Versions'
        ordering            = ['-created_at']
        unique_together     = [('taxon_group', 'version')]

    def __str__(self):
        return f'{self.taxon_group.name} v{self.version} [{self.status}]'
