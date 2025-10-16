# coding=utf-8
import datetime
import hashlib
import os
import json

from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from preferences import preferences
from rest_framework import serializers

from bims.enums import TaxonomicGroupCategory
from bims.models import DownloadRequest
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
    cites_listing = serializers.SerializerMethodField()
    invasion = serializers.SerializerMethodField()
    accepted_taxon = serializers.SerializerMethodField()

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
        if obj.origin:
            for value in Taxonomy.CATEGORY_CHOICES:
                if value[0] == obj.origin:
                    return value[1]
        return 'Unknown'

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
        if obj.invasion:
            return obj.invasion.category
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
            'species_group',
            'taxon',
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

@csrf_protect
@require_POST
def download_taxa_list(request):
    allowed_to_download = request.user.is_authenticated
    if not allowed_to_download and preferences.SiteSetting.is_public_taxa:
        allowed_to_download = True
    if not allowed_to_download:
        return HttpResponseForbidden('Not logged in')

    if request.content_type and "application/json" in request.content_type:
        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            data = {}
    else:
        data = request.POST.dict()

    output = (data.get('output') or 'csv').lower()
    taxon_group_id = data.get('taxonGroup')
    download_request_id = data.get('downloadRequestId', '')

    taxon_group = get_object_or_404(TaxonGroup, id=taxon_group_id)

    now = timezone.localtime()
    filter_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    filter_hash = hashlib.sha256(filter_str.encode('utf-8')).hexdigest()[:12]

    filename = (
        f"{taxon_group.name}-{now.year}-{now.month}-{now.day}-{now.hour}-{filter_hash}"
    ).replace(' ', '_')
    folder = settings.PROCESSED_CSV_PATH
    path_folder = os.path.join(settings.MEDIA_ROOT, folder)
    path_file = os.path.join(path_folder, filename)

    os.makedirs(path_folder, exist_ok=True)

    if os.path.exists(path_file):
        user_id = request.user.id if request.user.is_authenticated else None
        send_csv_via_email(
            user_id=user_id,
            csv_file=path_file,
            file_name=filename,
            approved=True
        )
    else:
        user_id = request.user.id if request.user.is_authenticated else None
        download_taxa_list_task.delay(
            data,
            csv_file=path_file,
            filename=filename,
            user_id=user_id,
            output=output,
            download_request_id=download_request_id,
            taxon_group_id=taxon_group_id
        )

    return JsonResponse({'status': 'processing', 'filename': filename})
