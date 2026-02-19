# coding=utf-8
import datetime
import os
import json

from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from rest_framework import serializers
from preferences import preferences

from bims.enums import TaxonomicGroupCategory
from bims.models.taxonomy import Taxonomy
from bims.models.taxon_group import TaxonGroup
from bims.models.iucn_status import IUCNStatus
from bims.models.taxon_extra_attribute import TaxonExtraAttribute
from bims.scripts.species_keys import BIOGRAPHIC_DISTRIBUTIONS
from bims.serializers.taxon_detail_serializer import TaxonHierarchySerializer
from bims.tasks.email_csv import send_csv_via_email
from bims.tasks.download_taxa_list import (
    download_taxa_list as download_taxa_list_task
)

SANPARKS_PROJECT_KEY = 'sanparks'
NATIONAL_NEMBA_LABEL = 'National NEMBA Status'
SANPARKS_NEMBA_STATUS_OPTIONS = [
    'Category 1a invasive',
    'Category 1b invasive',
    'Category 2 invasive',
    'Category 3 invasive',
    'Not listed',
]
SANPARKS_NEMBA_STATUS_MAP = {
    value.lower(): value for value in SANPARKS_NEMBA_STATUS_OPTIONS
}


def is_sanparks_project():
    return preferences.SiteSetting.project_name == SANPARKS_PROJECT_KEY


def apply_gbif_record_threshold(queryset, threshold=10000, limit=100):
    """
    Apply the GBIF record threshold rule to a queryset.

    If the queryset has more than `threshold` records, limit it to the first `limit` records.
    This is used to avoid performance issues when calculating aggregate statistics
    on large datasets.

    Args:
        queryset: Django QuerySet to potentially limit
        threshold: Maximum number of records before limiting (default: 10000)
        limit: Number of records to keep if threshold is exceeded (default: 100)

    Returns:
        QuerySet: Either the original queryset or a limited version
    """
    total_count = queryset.count()
    if total_count > threshold:
        return queryset[:limit]
    return queryset


class TaxaCSVSerializer(TaxonHierarchySerializer):

    taxon_rank = serializers.SerializerMethodField()
    taxon = serializers.SerializerMethodField()
    common_name = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    endemism = serializers.SerializerMethodField()
    conservation_status_global = serializers.SerializerMethodField()
    conservation_status_national = serializers.SerializerMethodField()
    on_gbif = serializers.SerializerMethodField()
    gbif_link = serializers.SerializerMethodField()
    gbif_coordinate_uncertainty_m = serializers.SerializerMethodField()
    gbif_coordinate_precision = serializers.SerializerMethodField()
    cites_listing = serializers.SerializerMethodField()
    invasion = serializers.SerializerMethodField()
    accepted_taxon = serializers.SerializerMethodField()
    scientific_name_and_authority = serializers.SerializerMethodField()

    def get_scientific_name_and_authority(self, obj: Taxonomy):
        return obj.scientific_name

    def get_accepted_taxon(self, obj: Taxonomy):
        if obj.accepted_taxonomy:
            return obj.accepted_taxonomy.canonical_name
        return ''

    def get_cites_listing(self, obj: Taxonomy):
        return obj.cites_listing

    def get_taxon_rank(self, obj):
        return obj.rank.capitalize()

    def get_taxon(self, obj):
        return obj.canonical_name

    def get_common_name(self, obj):
        vernacular_names = list(
            obj.vernacular_names.filter(
                language__istartswith='en'
            ).values_list('name', flat=True))
        if len(vernacular_names) == 0:
            return ''
        else:
            return vernacular_names[0]

    def get_origin(self, obj):
        return obj.origin.category if obj.origin else 'Unknown'

    def get_endemism(self, obj):
        return obj.endemism.name if obj.endemism else 'Unknown'

    def get_conservation_status_global(self, obj):
        if obj.iucn_status:
            for value in IUCNStatus.CATEGORY_CHOICES:
                if value[0] == obj.iucn_status.category:
                    return value[1]
            return 'Not evaluated'
        else:
            return 'Not evaluated'

    def get_conservation_status_national(self, obj: Taxonomy):
        if obj.national_conservation_status:
            for value in IUCNStatus.CATEGORY_CHOICES:
                if value[0] == obj.national_conservation_status.category:
                    return value[1]
            return 'Not evaluated'
        else:
            return ''

    def get_on_gbif(self, obj):
        return 'Yes' if obj.gbif_key else 'No'

    def get_gbif_link(self, obj):
        if obj.gbif_key:
            return 'https://www.gbif.org/species/{}'.format(
                obj.gbif_key
            )
        return '-'

    def get_invasion(self, obj: Taxonomy):
        status = (obj.invasion.category or '').strip() if obj.invasion else ''
        if is_sanparks_project():
            if not status:
                return ''
            normalized = SANPARKS_NEMBA_STATUS_MAP.get(status.lower())
            return normalized if normalized else ''
        return status

    def get_gbif_coordinate_uncertainty_m(self, obj: Taxonomy):
        """
        Get the lowest coordinate uncertainty in meters from GBIF sources.
        Rule: If total records > 10,000, use only first 100 records.
        """
        from bims.models import BiologicalCollectionRecord
        from django.db.models import Min

        # Get all GBIF records for this taxon
        gbif_records = BiologicalCollectionRecord.objects.filter(
            taxonomy=obj,
            site__harvested_from_gbif=True,
            site__coordinate_uncertainty_in_meters__isnull=False
        )

        # Check if we have any records
        if not gbif_records.exists():
            return ''

        # Apply the 10,000 threshold rule
        gbif_records = apply_gbif_record_threshold(gbif_records)

        # Get the minimum (lowest) uncertainty
        result = gbif_records.aggregate(
            min_uncertainty=Min('site__coordinate_uncertainty_in_meters')
        )

        min_uncertainty = result.get('min_uncertainty')
        if min_uncertainty is not None:
            return f"{min_uncertainty:.2f}"
        return ''

    def get_gbif_coordinate_precision(self, obj: Taxonomy):
        """
        Get the highest coordinate precision from GBIF sources.
        Rule: If total records > 10,000, use only first 100 records.
        Higher precision = smaller decimal value (e.g., 0.00001 is more precise than 0.01667)
        """
        from bims.models import BiologicalCollectionRecord
        from django.db.models import Min

        # Get all GBIF records for this taxon
        gbif_records = BiologicalCollectionRecord.objects.filter(
            taxonomy=obj,
            site__harvested_from_gbif=True,
            site__coordinate_precision__isnull=False
        )

        # Check if we have any records
        if not gbif_records.exists():
            return ''

        # Apply the 10,000 threshold rule
        gbif_records = apply_gbif_record_threshold(gbif_records)

        # Get the minimum (highest precision = smallest value)
        result = gbif_records.aggregate(
            max_precision=Min('site__coordinate_precision')
        )

        max_precision = result.get('max_precision')
        if max_precision is not None:
            return f"{max_precision:.6f}"
        return ''

    class Meta:
        model = Taxonomy
        fields = (
            'taxon_rank',
            'kingdom',
            'phylum',
            'class_name',
            'order',
            'family',
            'subfamily',
            'tribe',
            'subtribe',
            'genus',
            'subgenus',
            'species',
            'subspecies',
            'variety',
            'species_group',
            'taxon',
            'scientific_name_and_authority',
            'author',
            'taxonomic_status',
            'accepted_taxon',
            'common_name',
            'origin',
            'endemism',
            'invasion',
            'conservation_status_global',
            'conservation_status_national',
            'on_gbif',
            'gbif_link',
            'gbif_coordinate_uncertainty_m',
            'gbif_coordinate_precision',
            'fada_id',
            'cites_listing'
        )

    def __init__(self, *args, **kwargs):
        super(TaxaCSVSerializer, self).__init__(*args, **kwargs)
        self.context['headers'] = []
        self.context['additional_data'] = []
        self.context['tags'] = []
        self.context['additional_attributes_titles'] = []

    def _ensure_headers(self, keys):
        if 'headers' not in self.context:
            self.context['headers'] = list(keys)

    def _add_additional_attributes(self, instance, result):
        taxon_group = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name,
            taxonomies__in=[instance]
        ).first()

        if taxon_group:
            taxon_extra_attributes = TaxonExtraAttribute.objects.filter(
                taxon_group=taxon_group
            )
            for taxon_extra_attribute in taxon_extra_attributes:
                attribute_name = taxon_extra_attribute.name
                if attribute_name.lower().strip() == 'cites listing':
                    continue
                if attribute_name not in self.context['headers']:
                    self.context['headers'].append(attribute_name)
                    self.context['additional_attributes_titles'].append(
                        attribute_name
                    )
                if instance.additional_data:
                    result[attribute_name] = (
                        instance.additional_data.get(attribute_name, '')
                    )

    def _add_tags(self, instance, result):
        all_tags = list(instance.tags.all()) + list(instance.biographic_distributions.all())
        for tag in all_tags:
            tag_name = tag.name.strip()
            tag_value = 'Y'
            if '(?)' in tag_name:
                tag_value = '?'
                tag_name = tag_name.replace('(?)', '').strip()
            if tag_name not in self.context['headers']:
                self.context['headers'].append(tag_name)
                self.context['tags'].append(tag_name)
            result[tag_name] = tag_value

        for key in BIOGRAPHIC_DISTRIBUTIONS:
            if key not in self.context['headers']:
                self.context['headers'].append(key)
                self.context['tags'].append(key)
            if key not in result:
                result[key] = ''

    def to_representation(self, instance):
        result = super().to_representation(instance)
        self._ensure_headers(result.keys())
        self._add_additional_attributes(instance, result)
        self._add_tags(instance, result)
        return result

def download_taxa_list(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Not logged in')

    output = request.GET.get('output', 'csv')

    taxon_group_id = request.GET.get('taxonGroup')
    download_request_id = request.GET.get('downloadRequestId', '')
    taxon_group = TaxonGroup.objects.get(
        id=taxon_group_id
    )

    current_time = datetime.datetime.now()
    filter_hash = hash(json.dumps(request.GET.dict()))

    # Check if the file exists in the processed directory
    filename = (
        f'{taxon_group.name}-{current_time.year}-'
        f'{current_time.month}-{current_time.day}-'
        f'{current_time.hour}-{filter_hash}'
    ).replace(' ', '_')
    folder = settings.PROCESSED_CSV_PATH
    path_folder = os.path.join(
        settings.MEDIA_ROOT,
        folder
    )
    path_file = os.path.join(path_folder, filename)

    if not os.path.exists(path_folder):
        os.mkdir(path_folder)

    if os.path.exists(path_file):
        send_csv_via_email(
            user_id=request.user.id,
            csv_file=path_file,
            file_name=filename,
            approved=True
        )
    else:
        download_taxa_list_task.delay(
            request.GET.dict(),
            csv_file=path_file,
            filename=filename,
            user_id=request.user.id,
            output=output,
            download_request_id=download_request_id,
            taxon_group_id=taxon_group_id
        )

    return JsonResponse({
        'status': 'processing',
        'filename': filename
    })
