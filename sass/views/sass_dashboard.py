import json
from collections import OrderedDict
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import (
    Case, When, F, Count, Sum, FloatField,
    IntegerField, Q
)
from django.db.models.functions import Cast, Coalesce
from bims.models.chemical_record import ChemicalRecord
from bims.models.location_site import LocationSite
from bims.models.location_context import LocationContext
from bims.models.site_image import SiteImage
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.api_views.search import Search
from bims.serializers.chemical_records_serializer import \
    ChemicalRecordsSerializer
from sass.models import (
    SiteVisitTaxon,
    SiteVisitBiotopeTaxon,
    SassEcologicalCondition,
    SassEcologicalCategory
)
from sass.enums.chem_unit import ChemUnit


class SassDashboardView(TemplateView):
    template_name = 'sass_dashboard_single_site.html'
    location_site = LocationSite.objects.none()
    site_visit_taxa = SiteVisitTaxon.objects.none()
    use_combined_geo = False
    location_context = LocationContext.objects.none()

    def get_site_visit_taxon(self):
        filters = self.request.GET.dict()
        filters['validated'] = ''
        search = Search(filters)
        collection_records = search.process_search()
        self.site_visit_taxa = SiteVisitTaxon.objects.filter(
            id__in=collection_records,
            collection_date=F('site_visit__site_visit_date')
        )

    def get_sass_score_chart_data(self):
        data = {}
        summary = self.site_visit_taxa.annotate(
            date=F('collection_date'),
        ).values('date').annotate(
            count=Count('sass_taxon'),
            sass_score=Coalesce(Sum(Case(
                When(
                    condition=Q(site_visit__sass_version=5,
                                sass_taxon__sass_5_score__isnull=False,
                                taxon_abundance__isnull=False),
                    then='sass_taxon__sass_5_score'),
                When(
                    condition=Q(site_visit__sass_version=4,
                                sass_taxon__score__isnull=False,
                                taxon_abundance__isnull=False),
                    then='sass_taxon__score'),
                default=0),
            ), 0),
            sass_id=F('site_visit__id')
        ).annotate(
            aspt=Cast(F('sass_score'), FloatField()) / Cast(F('count'),
                                                            FloatField()),
        ).order_by('date')

        data['date_labels'] = (
            [dt.strftime('%d-%m-%Y')
             for dt in summary.values_list('date', flat=True)])
        data['taxa_numbers'] = list(
            summary.values_list('count', flat=True))
        data['sass_scores'] = list(
            summary.values_list('sass_score', flat=True))
        data['aspt_list'] = list(
            summary.values_list('aspt', flat=True))
        data['sass_ids'] = list(
            summary.values_list('sass_id', flat=True))
        return data

    def get_sass_taxon_table_data(self):
        data = {}
        latest_site_visit = (
            self.site_visit_taxa.
            order_by('-site_visit__site_visit_date')[0].site_visit
        )
        sass_taxon_data = (
            self.site_visit_taxa.filter(
                site_visit=latest_site_visit,
                taxonomy__taxongroup__category=(
                    TaxonomicGroupCategory.SASS_TAXON_GROUP.name
                )
            ).annotate(
                sass_taxon_name=F('sass_taxon__taxon_sass_4'),
                sass_score=Case(
                    When(
                        condition=Q(site_visit__sass_version=5,
                                    sass_taxon__sass_5_score__isnull=False),
                        then='sass_taxon__sass_5_score'),
                    default='sass_taxon__score'
                ),
                display_order=Case(
                    When(
                        condition=Q(
                            site_visit__sass_version=5,
                            sass_taxon__display_order_sass_5__isnull=False),
                        then='sass_taxon__display_order_sass_5'),
                    default='sass_taxon__display_order_sass_4'
                ),
            ).values(
                'sass_taxon_id',
                'taxonomy__canonical_name',
                'taxonomy__id',
                'taxonomy__taxongroup__name',
                'taxon_abundance__abc',
                'sass_taxon_name',
                'sass_score',
                'display_order'
            )
            .order_by('display_order')
        )

        biotope_data = (
            SiteVisitBiotopeTaxon.objects.filter(
                sass_taxon__in=self.site_visit_taxa.values_list('sass_taxon'),
                site_visit=latest_site_visit).values(
                'biotope__name', 'sass_taxon', 'taxon_abundance__abc')
        )
        data['sass_taxon_data'] = json.dumps(list(sass_taxon_data))
        data['biotope_data'] = json.dumps(list(biotope_data))
        data['site_visit_date'] = latest_site_visit.site_visit_date
        return data

    def get_sensitivity_chart_data(self):
        """
        Get data for sensitivity chart, only for latest data
        Ordered by :
        Highly tolerant = 1 - 3
        Tolerant = 4 - 7
        Sensitive = 8 - 11
        Highly Sensitive 12 - 15
        :return: dict of sensitivity chart data
        {
            'highly_tolerant': 1,
            'tolerant': 1,
            'sensitive': 1,
            'highly_sensitive': 1
        }
        """
        latest_site_visit = (
            self.site_visit_taxa.order_by(
                '-site_visit__site_visit_date')[0].site_visit
        )
        sensitivity_data = (
            self.site_visit_taxa.filter(
                site_visit=latest_site_visit
            ).annotate(
                sass_score=Case(
                    When(site_visit__sass_version=5,
                         then='sass_taxon__sass_5_score'),
                    When(site_visit__sass_version=4,
                         then='sass_taxon__score'),
                    default='sass_taxon__sass_5_score',
                    output_field=IntegerField()
                ),
            ).annotate(
                highly_tolerant_value=Case(
                    When(
                        condition=Q(
                            sass_score__gte=1, sass_score__lte=3),
                        then=1),
                    output_field=IntegerField()
                ),
                tolerant_value=Case(
                    When(
                        condition=Q(
                            sass_score__gte=4, sass_score__lte=7),
                        then=1),
                    output_field=IntegerField()
                ),
                sensitive_value=Case(
                    When(
                        condition=Q(
                            sass_score__gte=8, sass_score__lte=11),
                        then=1),
                    output_field=IntegerField()
                ),
                highly_sensitive_value=Case(
                    When(
                        condition=Q(
                            sass_score__gte=12, sass_score__lte=15),
                        then=1),
                    output_field=IntegerField()
                ),
            ).aggregate(
                highly_tolerant=Coalesce(Sum('highly_tolerant_value'), 0),
                tolerant=Coalesce(Sum('tolerant_value'), 0),
                sensitive=Coalesce(Sum('sensitive_value'), 0),
                highly_sensitive=Coalesce(Sum('highly_sensitive_value'), 0)
            )
        )

        return sensitivity_data

    def get_biotope_ratings_chart_data(self):
        """
        Get data for biotope ratings chart
        :return: dict of biotope ratings
        """
        data = {}

        biotope_ratings = self.site_visit_taxa.filter(
            site_visit__sass_biotope_fraction__sass_biotope__biotope_form=1
        ).annotate(
            date=F('site_visit__site_visit_date'),
            rate=F('site_visit__sass_biotope_fraction__rate__rate'),
            biotope_name=F(
                'site_visit__sass_biotope_fraction__sass_biotope__name')
        ).values('date', 'rate', 'biotope_name').order_by(
            'site_visit__site_visit_date',
            'site_visit__sass_biotope_fraction__sass_biotope__display_order'
        ).distinct()

        biotope_labels = []

        for rating_data in biotope_ratings:
            date = rating_data['date'].strftime('%d-%m-%Y')
            if date not in data:
                data[date] = {}
            rate = rating_data['rate']
            biotope = rating_data['biotope_name'].encode('utf-8')
            if not rate:
                rate = 0
            data[date][biotope] = rate
            if biotope not in biotope_labels:
                biotope_labels.append(biotope)

        return {
            'rating_data': data,
            'biotope_labels': biotope_labels
        }

    def get_ecological_chart_data(self):
        chart_data = {}
        try:
            eco_region = self.location_context.value_from_key(
                'eco_region_1'
            )
            geo_class = self.location_context.value_from_key(
                'geo_class'
            )
            # Fix eco_region name
            eco_region_splits = eco_region.split(' ')
            if eco_region_splits[0].isdigit():
                eco_region_splits.pop(0)
                eco_region = ' '.join(eco_region_splits)

            ecological_conditions = SassEcologicalCondition.objects.filter(
                ecoregion_level_1__icontains=eco_region.strip(),
                geomorphological_zone__icontains=geo_class.strip()
            )

            use_combined_geo = False
            if not ecological_conditions:
                use_combined_geo = True
            if (
                    not use_combined_geo and
                    not ecological_conditions.filter(
                        sass_score_precentile__isnull=False,
                        aspt_score_precentile__isnull=False).exists()
            ):
                use_combined_geo = True
            if use_combined_geo:
                # check Combined data
                geo_class = 'combined'
                ecological_conditions = SassEcologicalCondition.objects.filter(
                    ecoregion_level_1__icontains=eco_region,
                    geomorphological_zone__icontains=geo_class
                )
            self.use_combined_geo = use_combined_geo

            ecological_conditions = ecological_conditions.annotate(
                ecological_name=F('ecological_category__name'),
                ecological_category_name=F('ecological_category__category'),
                ecological_colour=F('ecological_category__colour'),
            ).values(
                'ecological_name',
                'ecological_category_name',
                'ecological_colour',
                'sass_score_precentile',
                'aspt_score_precentile'
            ).order_by('ecological_category__order')
            chart_data = list(ecological_conditions)
            if chart_data:
                lowest_category = SassEcologicalCategory.objects.filter(
                    Q(category__icontains='e') |
                    Q(category__icontains='f')
                )
                if lowest_category.exists():
                    lowest_category = lowest_category[0]
                    chart_data.append({
                        'ecological_name': lowest_category.name,
                        'ecological_category_name': 'E/F',
                        'ecological_colour': lowest_category.colour,
                        'sass_score_precentile': 0,
                        'aspt_score_precentile': 0.0
                    })
            chart_data = json.dumps(chart_data)
        except (KeyError, TypeError):
            pass
        return chart_data

    def ordering_catchment_data(self, river_catchment):
        display_order = {
            'primary_catchment_area': 0,
            'secondary_catchment_area': 1,
            'tertiary_catchment_area': 2,
            'quaternary_catchment_area': 3,
            'quinary_catchment_area': 4,
        }

        for key, value in river_catchment.items():
            if key not in display_order:
                value['display_order'] = 5
            else:
                value['display_order'] = display_order[value['key']]

        ordered_dict = OrderedDict(
            sorted(
                river_catchment.items(),
                key=lambda (k, v): (v['display_order'], k)))
        return ordered_dict

    def get_context_data(self, **kwargs):
        context = super(SassDashboardView, self).get_context_data(**kwargs)
        self.get_site_visit_taxon()
        context['coord'] = [
            self.location_site.get_centroid().x,
            self.location_site.get_centroid().y
        ]
        context['site_code'] = self.location_site.site_code
        context['site_id'] = self.location_site.id
        try:
            context['site_image'] = (
                SiteImage.objects.filter(site=self.location_site))
        except SiteImage.DoesNotExist:
            pass
        context['original_site_code'] = self.location_site.legacy_site_code
        context['original_river_name'] = self.location_site.legacy_river_name
        site_description = self.location_site.site_description
        if not site_description:
            site_description = self.location_site.name
        context['site_description'] = site_description
        try:
            context['river'] = self.location_site.river.name
        except AttributeError:
            context['river'] = '-'

        if not self.site_visit_taxa:
            context['sass_exists'] = False
            return context

        context['sass_exists'] = True

        context['sass_score_chart_data'] = self.get_sass_score_chart_data()
        context['sass_taxon_table_data'] = self.get_sass_taxon_table_data()
        context['sensitivity_chart_data'] = self.get_sensitivity_chart_data()
        context['ecological_chart_data'] = self.get_ecological_chart_data()
        context['biotope_ratings_chart_data'] = (
            self.get_biotope_ratings_chart_data()
        )

        collection_with_references = self.site_visit_taxa.exclude(
                source_reference__isnull=True
        ).distinct('source_reference')

        source_references = collection_with_references.source_references()

        context['source_references'] = json.dumps(source_references)

        river_catchments = self.location_context.values_from_group(
            'river_catchment_areas_group'
        )
        # river_catchments = self.ordering_catchment_data(river_catchments)
        context['river_catchments'] = json.dumps(river_catchments)
        context['river_ecoregion_group'] = (
            json.dumps(self.location_context.values_from_group(
                'river_ecoregion_group'
            ))
        )
        context['political_boundary'] = (
            json.dumps(self.location_context.values_from_group(
                'political_boundary_group'
            ))
        )
        context['geomorphological_group'] = (
            json.dumps(self.location_context.values_from_group(
                'geomorphological_group'
            ))
        )
        context['freshwater_ecoregion_of_the_world'] = (
            json.dumps(self.location_context.values_from_group(
                'freshwater_ecoregion_of_the_world'
            ))
        )
        context['use_combined_geo'] = self.use_combined_geo
        refined_geomorphological = '-'
        if self.location_site.refined_geomorphological:
            refined_geomorphological = (
                self.location_site.refined_geomorphological
            )
        context['refined_geomorphological'] = refined_geomorphological
        context['original_geomorphological'] = (
            self.location_site.original_geomorphological
        )

        context['eco_geo'] = (
            json.dumps(self.location_context.values_from_group(
                'eco_geo_group'
            ))
        )
        context['wma'] = (
            json.dumps(self.location_context.values_from_group(
                'water_management_area'
            ))
        )

        list_chems = {}
        if self.location_site.id:
            list_chems_code = [
                'COND',
                'TEMP',
                'PH',
                'DO'
            ]
            chems = ChemicalRecord.objects.filter(
                Q(location_site_id=self.location_site.id) |
                Q(survey__site_id=self.location_site.id)
            )
            x_label = []
            for chem in list_chems_code:
                chem_name = chem.lower().replace('-n', '').upper()
                qs = chems.filter(chem__chem_code=chem).order_by('date')
                if not qs.exists():
                    continue
                value = ChemicalRecordsSerializer(qs, many=True)

                # Get chemical unit
                try:
                    chem_unit = ChemUnit[qs[0].chem.chem_unit].value
                except KeyError:
                    chem_unit = qs[0].chem.chem_unit

                data = {
                    'unit': chem_unit,
                    'name': qs[0].chem.chem_description,
                    'values': value.data
                }
                for val in value.data:
                    if val['str_date'] not in x_label:
                        x_label.append(val['str_date'])
                try:
                    list_chems[chem_name].append({chem: data})
                except KeyError:
                    list_chems[chem_name] = [{chem: data}]
        context['chemical_records'] = json.dumps(list_chems)
        context['is_chem_exists'] = len(list_chems) > 1

        return context

    def get(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
        if not site_id or not request.GET or not request.GET.get(
            'siteId', None):
            raise Http404()
        self.location_site = get_object_or_404(
            LocationSite,
            pk=site_id
        )
        self.location_context = LocationContext.objects.filter(
            site=self.location_site
        )
        return super(SassDashboardView, self).get(request, *args, **kwargs)
