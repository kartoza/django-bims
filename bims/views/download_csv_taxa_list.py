# coding=utf-8
import csv

from django.http import HttpResponse
from rest_framework import serializers
from bims.models.taxonomy import Taxonomy
from bims.models.taxon_group import TaxonGroup
from bims.models.iucn_status import IUCNStatus
from bims.api_views.taxon import TaxaList


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
        if 'additional_data' not in self.context:
            self.context['additional_data'] = []

        for additional_data_key in self.context['additional_data']:
            if additional_data_key not in result:
                result[additional_data_key] = ''

        if instance.additional_data:
            for key, value in instance.additional_data.items():
                key_title = key.lower().replace(' ', '_')
                # Skip class and link in the additional data
                if key_title == 'class' or key_title == 'link':
                    continue
                if key_title not in self.context['headers']:
                    self.context['headers'].append(key_title)
                if (
                        key_title not in self.context['additional_data'] and
                        key not in result):
                    self.context['additional_data'].append(key_title)
                if key not in result:
                    result[key_title] = value
        return result


def download_csv_taxa_list(request):
    taxon_group_id = request.GET.get('taxonGroup')
    taxon_group = TaxonGroup.objects.get(
        id=taxon_group_id
    )
    taxa_list = TaxaList.get_taxa_by_parameters(request)

    taxa_serializer = TaxaCSVSerializer(
        taxa_list,
        many=True
    )

    rows = taxa_serializer.data
    headers = taxa_serializer.context['headers']

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename="' + taxon_group.name + '.csv"'

    writer = csv.writer(response)
    updated_headers = []

    for header in headers:
        if header == 'class_name':
            header = 'class'
        elif header == 'taxon_rank':
            header = 'Taxon Rank'
        elif header == 'common_name':
            header = 'Common Name'
        header = header.replace('_or_', '/')
        if not header.istitle():
            header = header.replace('_', ' ').capitalize()
        updated_headers.append(header)
    writer.writerow(updated_headers)

    for taxon_row in rows:
        writer.writerow([value for key, value in taxon_row.items()])

    return response
