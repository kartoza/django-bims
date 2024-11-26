# coding=utf-8
import datetime
import hashlib
import io
import os
import json

from braces.views import LoginRequiredMixin
from django.db.models import F, Case, When, Value, Count
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.conf import settings
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

from reportlab.platypus import SimpleDocTemplate
from rest_framework import serializers, status
from rest_framework.views import APIView

from bims.enums import TaxonomicGroupCategory
from bims.models.taxonomy import Taxonomy
from bims.models.taxon_group import TaxonGroup
from bims.models.iucn_status import IUCNStatus
from bims.models.taxon_extra_attribute import TaxonExtraAttribute
from bims.tasks.email_csv import send_csv_via_email
from bims.tasks.download_taxa_list import (
    download_csv_taxa_list as download_csv_taxa_list_task
)
from bims.models.cites_listing_info import CITESListingInfo


class TaxaCSVSerializer(serializers.ModelSerializer):

    taxon_rank = serializers.SerializerMethodField()
    kingdom = serializers.SerializerMethodField()
    phylum = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    genus = serializers.SerializerMethodField()
    family = serializers.SerializerMethodField()
    species = serializers.SerializerMethodField()
    sub_species = serializers.SerializerMethodField()
    taxon = serializers.SerializerMethodField()
    scientific_name_and_authority = serializers.SerializerMethodField()
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

    def get_species(self, obj: Taxonomy):
        species_name = obj.species_name
        if species_name:
            genus_name = obj.genus_name
            if genus_name:
                species_name = species_name.replace(genus_name, '')
            return species_name.strip()
        return species_name

    def get_sub_species(self, obj: Taxonomy):
        sub_species_name = obj.sub_species_name
        if sub_species_name:
            genus_name = obj.genus_name
            if genus_name:
                sub_species_name = sub_species_name.replace(genus_name, '', 1)
            species_name = obj.species_name
            if species_name:
                sub_species_name = sub_species_name.replace(species_name, '', 1)
        return sub_species_name

    def get_taxon(self, obj):
        return obj.canonical_name

    def get_scientific_name_and_authority(self, obj):
        return obj.scientific_name

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
            'genus',
            'species',
            'sub_species',
            'taxon',
            'taxonomic_status',
            'accepted_taxon',
            'scientific_name_and_authority',
            'common_name',
            'origin',
            'endemism',
            'invasion',
            'conservation_status_global',
            'conservation_status_national',
            'on_gbif',
            'gbif_link',
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

    def to_representation(self, instance):
        result = super().to_representation(instance)
        self._ensure_headers(result.keys())
        self._add_additional_attributes(instance, result)
        self._add_tags(instance, result)
        return result


def download_csv_taxa_list(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Not logged in')

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
        download_csv_taxa_list_task.delay(
            request.GET.dict(),
            csv_file=path_file,
            filename=filename,
            user_id=request.user.id,
            download_request_id=download_request_id
        )

    return JsonResponse({
        'status': 'processing',
        'filename': filename
    })


class DownloadPdfTaxaList(LoginRequiredMixin, APIView):

    def generate_color(self, key, alpha=1):
        hash_obj = hashlib.sha1(key.encode())
        hash_num = int(hash_obj.hexdigest(), 16)

        r = (hash_num & 0xFF0000) >> 16
        g = (hash_num & 0x00FF00) >> 8
        b = (hash_num & 0x0000FF)
        return colors.toColor(f'rgba({r},{g},{b},{alpha})')

    def draw_pie_with_legend(self, data, title):
        drawing = Drawing(400, 200)

        pie = Pie()
        pie.x = 50
        pie.y = 15
        pie.width = 120
        pie.height = 120
        pie.data = list(data.values())
        pie.labels = list(data.keys())
        pie.slices.strokeWidth = 0.5
        pie.slices.strokeColor = colors.white
        pie.slices.label_visible = False

        for i in range(len(data)):
            pie.slices[i].popout = 5

        drawing.add(
            String(100, 180, title, fontSize=15, textAnchor='middle', fontName='Helvetica'))

        legend = Legend()
        legend.x = 180
        legend.y = 75
        legend.dx = 8
        legend.dy = 8
        legend.fontName = 'Helvetica'
        legend.fontSize = 8
        legend.boxAnchor = 'w'
        legend.columnMaximum = 10
        legend.strokeWidth = 0.5
        legend.strokeColor = colors.black
        legend.deltax = 75
        legend.deltay = 15
        legend.autoXPadding = 5
        legend.autoYPadding = 10
        legend.yGap = 0
        legend.dxTextSpace = 5
        legend.alignment = 'right'
        legend.dividerLines = 1 | 2 | 4
        legend.dividerOffsY = 7
        legend.subCols.rpad = 30

        pie.slices.fillColor = None
        legend.colorNamePairs = []
        for i, key in enumerate(list(data.keys())):
            color = self.generate_color(key)
            pie.slices[i].fillColor = color
            legend.colorNamePairs.append(
                (color, f'{pie.labels[i]} : {data[pie.labels[i]]}'))

        drawing.add(pie)
        drawing.add(legend)

        return drawing

    def get(self, request):
        if not request.user.is_authenticated:
            return HttpResponseForbidden('Not logged in')

        taxon_group_id = request.GET.get('taxonGroup')
        if not taxon_group_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Taxon group ID must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
        except TaxonGroup.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Taxon group not found'
            }, status=status.HTTP_404_NOT_FOUND)

        taxonomies = taxon_group.taxonomies.all()

        endemism_summary = dict(taxonomies.annotate(
            value=Case(When(endemism__isnull=False,
                            then=F('endemism__name')),
                       default=Value('Unknown'))
        ).values('value').annotate(
            count=Count('value')).values_list('value', 'count'))

        origin_dict = {
            'alien': 'Non-Native',
            'indigenous': 'Native',
            'unknown': 'Unknown',
        }
        origin_summary = dict(taxonomies.annotate(
            value=Case(When(origin='',
                            then=Value('unknown')),
                       default=F('origin'))
        ).values('value').annotate(
            count=Count('value')).values_list('value', 'count'))

        origin_summary_updated = {}
        for origin_data in origin_summary.keys():
            origin_summary_updated[
                origin_dict[origin_data]
            ] = origin_summary[origin_data]

        # Create a PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="taxa_list.pdf"'

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(letter[1], letter[0]),
            rightMargin=5,
            leftMargin=5,
            topMargin=10,
            bottomMargin=10)

        story = []

        drawing = Drawing(400, 50)

        drawing.add(
            String(100, 20,
                   taxon_group.name,
                   fontSize=20, fontName='Helvetica'))

        story.append(drawing)
        story.append(self.draw_pie_with_legend(endemism_summary, 'Endemism'))
        story.append(self.draw_pie_with_legend(origin_summary_updated, 'Origin'))

        doc.build(story)

        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response
