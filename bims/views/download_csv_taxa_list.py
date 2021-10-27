# coding=utf-8
import datetime
import os
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from rest_framework import serializers

from bims.enums import TaxonomicGroupCategory
from bims.models.taxonomy import Taxonomy
from bims.models.taxon_group import TaxonGroup
from bims.models.iucn_status import IUCNStatus
from bims.models.taxon_extra_attribute import TaxonExtraAttribute
from bims.api_views.csv_download import send_csv_via_email
from bims.tasks.download_taxa_list import (
    download_csv_taxa_list as download_csv_taxa_list_task
)


class TaxaCSVSerializer(serializers.ModelSerializer):

    taxon_rank = serializers.SerializerMethodField()
    kingdom = serializers.SerializerMethodField()
    phylum = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    genus = serializers.SerializerMethodField()
    family = serializers.SerializerMethodField()
    species = serializers.SerializerMethodField()
    taxon = serializers.SerializerMethodField()
    scientific_name_and_authority = serializers.SerializerMethodField()
    common_name = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    endemism = serializers.SerializerMethodField()
    conservation_status = serializers.SerializerMethodField()
    on_gbif = serializers.SerializerMethodField()
    gbif_link = serializers.SerializerMethodField()

    def get_taxon_rank(self, obj):
        return obj.rank.capitalize()

    def get_kingdom(self, obj):
        return obj.kingdom_name

    def get_phylum(self, obj):
        return obj.phylum_name

    def get_class_name(self, obj):
        return obj.class_name

    def get_order(self, obj):
        return obj.order_name

    def get_genus(self, obj):
        return obj.genus_name

    def get_family(self, obj):
        return obj.family_name

    def get_species(self, obj):
        return obj.species_name

    def get_taxon(self, obj):
        return obj.canonical_name

    def get_scientific_name_and_authority(self, obj):
        return obj.scientific_name

    def get_common_name(self, obj):
        vernacular_names = obj.vernacular_names.all()
        return vernacular_names[0] if vernacular_names else 'Unknown'

    def get_origin(self, obj):
        if obj.origin:
            for value in Taxonomy.CATEGORY_CHOICES:
                if value[0] == obj.origin:
                    return value[1]
        return 'Unknown'

    def get_endemism(self, obj):
        return obj.endemism.name if obj.endemism else 'Unknown'

    def get_conservation_status(self, obj):
        if obj.iucn_status:
            for value in IUCNStatus.CATEGORY_CHOICES:
                if value[0] == obj.iucn_status.category:
                    return value[1]
            return 'Not evaluated'
        else:
            return 'Not evaluated'

    def get_on_gbif(self, obj):
        return 'Yes' if obj.gbif_key else 'No'

    def get_gbif_link(self, obj):
        if obj.gbif_key:
            return 'https://www.gbif.org/species/{}'.format(
                obj.gbif_key
            )
        return '-'

    class Meta:
        model = Taxonomy
        fields = (
            'taxon_rank',
            'kingdom',
            'phylum',
            'class_name',
            'order',
            'family',
            'genus',
            'species',
            'taxon',
            'scientific_name_and_authority',
            'common_name',
            'origin',
            'endemism',
            'conservation_status',
            'on_gbif',
            'gbif_link'
        )

    def __init__(self, *args, **kwargs):
        super(TaxaCSVSerializer, self).__init__(*args, **kwargs)
        self.context['headers'] = []
        self.context['additional_data'] = []

    def to_representation(self, instance):
        result = super(
            TaxaCSVSerializer, self).to_representation(
            instance)
        if 'headers' not in self.context:
            self.context['headers'] = list(result.keys())

        taxon_group = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name,
            taxonomies__in=[instance]).first()

        if taxon_group:
            taxon_extra_attributes = TaxonExtraAttribute.objects.filter(
                taxon_group=taxon_group
            )
            if taxon_extra_attributes.exists():
                for taxon_extra_attribute in taxon_extra_attributes:
                    taxon_attribute_name = taxon_extra_attribute.name
                    key_title = taxon_attribute_name.lower().replace(' ', '_')
                    if key_title not in self.context['headers']:
                        self.context['headers'].append(key_title)
                    if taxon_attribute_name in instance.additional_data:
                        result[key_title] = (
                            instance.additional_data[taxon_attribute_name]
                        )
                    else:
                        result[key_title] = ''

        return result


def download_csv_taxa_list(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Not logged in')

    taxon_group_id = request.GET.get('taxonGroup')
    taxon_group = TaxonGroup.objects.get(
        id=taxon_group_id
    )

    current_time = datetime.datetime.now()

    # Check if the file exists in the processed directory
    filename = (
        f'{taxon_group}-{current_time.year}-'
        f'{current_time.month}-{current_time.day}-'
        f'{current_time.hour}-{current_time.minute}'
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
            user=request.user,
            csv_file=path_file,
            file_name=filename
        )
    else:
        download_csv_taxa_list_task.delay(
            request.GET.dict(),
            csv_file=path_file,
            filename=filename,
            user_id=request.user.id
        )

    return JsonResponse({
        'status': 'processing',
        'filename': filename
    })
