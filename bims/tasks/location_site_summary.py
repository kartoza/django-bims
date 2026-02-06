import json
import time

from celery import shared_task, current_task
from django.db.models import Q, F, Count, Case, When, Value
from django.db.models.functions import Coalesce, ExtractYear
from preferences import preferences
from sorl.thumbnail import get_thumbnail


COUNT = 'count'
ORIGIN = 'origin'
TOTAL_RECORDS = 'total_records'
TAXA_OCCURRENCE = 'taxa_occurrence'
CATEGORY_SUMMARY = 'category_summary'
TAXONOMY_NAME = 'name'
BIODIVERSITY_DATA = 'biodiversity_data'
SITE_DETAILS = 'site_details'
OCCURRENCE_DATA = 'occurrence_data'
IUCN_NAME_LIST = 'iucn_name_list'
ORIGIN_NAME_LIST = 'origin_name_list'
TAXA_GRAPH = 'taxa_graph'
ORIGIN_OCCURRENCE = 'origin_occurrence'
CONS_STATUS_OCCURRENCE = 'cons_status_occurrence'
SOURCE_REFERENCES = 'source_references'
CHEMICAL_RECORDS = 'chemical_records'
SURVEY = 'survey'


@shared_task(bind=True, name='bims.tasks.generate_location_site_summary', queue='search')
def generate_location_site_summary(
        self, filters, search_process_id):
    from bims.models import (
        IUCNStatus, Taxonomy, BiologicalCollectionRecord, TaxonGroup, DashboardConfiguration,
        ChemicalRecord, Survey, SiteImage, SEARCH_FINISHED, Biotope, SearchProcess
    )
    from bims.api_views.location_site_dashboard import (
        PER_YEAR_FREQUENCY, PER_MONTH_FREQUENCY
    )
    from bims.api_views.search import CollectionSearch
    from bims.enums import TaxonomicGroupCategory
    from bims.serializers.chemical_records_serializer import ChemicalRecordsSerializer
    from bims.utils.location_site import overview_site_detail
    from bims.utils.search_process import create_search_process_file

    called_directly = current_task.request.called_directly
    if not called_directly:
        self.update_state(
            state='PROGRESS',
            meta={'process': 'Generating location site summary'})

    search_process = SearchProcess.objects.get(id=search_process_id)
    times = {}
    filters = dict(filters)
    search = CollectionSearch(
        filters,
        search_process.requester.id if search_process.requester else None)

    start_time = time.time()
    collection_results = search.process_search()

    def multiple_site_details(collection_records):
        """
        Get detail overview for multiple site
        :param collection_records: biological colleciton records
        :return: dict of details
        """
        summary = {
            'overview': {}
        }

        summary['overview']['Occurences'] = (
            collection_records.count()
        )
        summary['overview']['Number of Sites'] = (
            collection_records.distinct('site').count()
        )
        summary['overview']['Number of Taxa'] = (
            collection_records.distinct('taxonomy').count()
        )

        return summary

    def site_taxa_occurrences_per_date(collection_records):
        """
        Get occurrence data for charts based on the date sampled
        :param collection_records: collection record queryset
        :return: dict of taxa occurrence data for line graph
        """
        taxa_occurrence_data = collection_records.values('collection_date').annotate(
            count=Count('collection_date')
        ).order_by('collection_date')
        result = dict()
        result['occurrences_line_chart'] = {
            'values': [],
            'keys': [],
            'title': 'Occurrences per Date Sampled'
        }
        for data in taxa_occurrence_data:
            formatted_date = data['collection_date'].strftime('%Y-%m-%d')
            result['occurrences_line_chart']['keys'].append(formatted_date)
            result['occurrences_line_chart']['values'].append(data['count'])
        return result

    def parse_string(string_in):
        if not string_in:
            return '-'
        else:
            if isinstance(string_in, str):
                return string_in.strip()
            return str(string_in)

    def get_number_of_records_and_taxa(records_collection):
        records_collection.annotate()
        result = dict()
        number_of_occurrence_records = records_collection.count()
        number_of_unique_taxa = records_collection.values(
            'taxonomy_id').distinct().count()
        result['Number of Occurrences'] = parse_string(
            number_of_occurrence_records)
        result['Number of Taxa'] = parse_string(number_of_unique_taxa)
        return result

    def site_taxa_occurrences_per_year(collection_records):
        """
        Get occurrence data for charts
        :param: collection_records: collection record queryset
        :return: dict of taxa occurrence data for stacked bar graph
        """
        taxa_occurrence_data = collection_records.annotate(
            year=ExtractYear('collection_date'),
        ).values('year'
                 ).annotate(count=Count('year')
                            ).values('year', 'count'
                                     ).order_by('year')
        result = dict()
        result['occurrences_line_chart'] = {}
        result['occurrences_line_chart']['values'] = list(
            taxa_occurrence_data.values_list('count', flat=True))
        result['occurrences_line_chart']['keys'] = list(
            taxa_occurrence_data.values_list('year', flat=True))
        result['occurrences_line_chart']['title'] = 'Occurrences'
        return result

    def conservation_status_data(national, collection_records):
        status_field_path = (
            'taxonomy__national_conservation_status__category'
            if national else 'taxonomy__iucn_status__category'
        )
        cons_status_data = collection_records.annotate(
            status=Coalesce(F(status_field_path), Value('NE'))
        ).values('status').annotate(
            count=Count('status')
        ).order_by('status')
        keys = [item['status'] for item in cons_status_data]
        values = [item['count'] for item in cons_status_data]
        return [keys, values]

    def get_biodiversity_data(collection_records):
        biodiversity_data = {}
        biodiversity_data['times'] = {}
        biodiversity_data['species'] = {}
        biodiversity_data['species']['origin_chart'] = {}
        biodiversity_data['species']['cons_status_chart'] = {}
        biodiversity_data['species']['endemism_chart'] = {}
        biodiversity_data['species']['sampling_method_chart'] = {}
        biodiversity_data['species']['biotope_chart'] = {}

        start_time = time.time()
        origin_data = collection_records.annotate(
            name=Case(When(taxonomy__origin='',
                           then=Value('Unknown')),
                      default=F('taxonomy__origin'))
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        ).order_by(
            'name'
        )
        biodiversity_data['species']['origin_chart'] = {
            'keys': [item['name'] for item in origin_data],
            'data': [item['count'] for item in origin_data]
        }
        biodiversity_data['times']['origin_by_name_data'] = time.time() - start_time

        start_time = time.time()
        local_conservation_status_data = conservation_status_data(
            False,
            collection_records
        )

        global_iucn_colors = dict(IUCNStatus.objects.filter(national=False).values_list(
            'category',
            'colour'
        ))
        biodiversity_data['species']['cons_status_chart']['data'] = local_conservation_status_data[1]
        biodiversity_data['species']['cons_status_chart']['keys'] = local_conservation_status_data[0]
        biodiversity_data['species']['cons_status_chart']['colours'] = [
            global_iucn_colors[x] for x in local_conservation_status_data[0]
        ]

        national_iucn_colors = dict(IUCNStatus.objects.filter(national=True).values_list(
            'category',
            'colour'
        ))
        national_conservation_status_data = conservation_status_data(
            True,
            collection_records
        )

        if preferences.SiteSetting.project_name != "fbis_africa":
            biodiversity_data['species']['cons_status_national_chart'] = {}
            biodiversity_data['species']['cons_status_national_chart']['data'] = (
                national_conservation_status_data[1]
            )
            biodiversity_data['species']['cons_status_national_chart']['keys'] = (
                national_conservation_status_data[0]
            )
            biodiversity_data['species']['cons_status_national_chart']['colours'] = [
                national_iucn_colors[x] for x in national_conservation_status_data[0]
            ]

        biodiversity_data['times']['conservation_status_data'] = time.time() - start_time

        start_time = time.time()
        endemism_data = collection_records.annotate(
            name=Case(When(taxonomy__endemism__name__isnull=False,
                           then=F('taxonomy__endemism__name')),
                      default=Value('Unknown'))
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        ).order_by(
            'name'
        )
        biodiversity_data['species']['endemism_chart'] = {
            'keys': [item['name'] for item in endemism_data],
            'data': [item['count'] for item in endemism_data]
        }
        biodiversity_data['times']['endemism_status_data'] = time.time() - start_time

        # Sampling method
        start_time = time.time()
        sampling_data = collection_records.annotate(
            name=Coalesce(
                F('sampling_method__sampling_method'), Value('Unknown'))
        ).values('name').annotate(count=Count('name')).order_by('name')
        biodiversity_data['species']['sampling_method_chart'] = {
            'keys': [item['name'] for item in sampling_data],
            'data': [item['count'] for item in sampling_data]
        }
        biodiversity_data['times']['sampling_method_chart'] = time.time() - start_time

        # Biotope
        start_time = time.time()
        biotope_data = Biotope.objects.filter(
            biologicalcollectionrecord__id__in=collection_records.values_list('id', flat=True)
        ).values('name').annotate(count=Count('name')).order_by('name')
        biotope_keys = [item['name'] for item in biotope_data]
        biotope_counts = [item['count'] for item in biotope_data]
        unspecified_biotope_count = collection_records.filter(biotope__isnull=True).count()
        if unspecified_biotope_count > 0:
            biotope_keys.append('Unknown')
            biotope_counts.append(unspecified_biotope_count)
        biodiversity_data['species']['biotope_chart'] = {
            'keys': biotope_keys,
            'data': biotope_counts
        }
        biodiversity_data['times']['biotope_chart'] = time.time() - start_time

        return biodiversity_data

    def occurrence_data(collection_records):
        """
        Get occurrence data
        :param collection_records: collection search results
        :return: list of occurrence data
        """
        occurrence_table_data = collection_records.annotate(
            taxon=F('taxonomy__scientific_name'),
            origin=Case(When(taxonomy__origin='',
                             then=Value('Unknown')),
                        default=F('taxonomy__origin')),
            cons_status=Case(
                When(taxonomy__iucn_status__isnull=False,
                     then=F('taxonomy__iucn_status__category')),
                default=Value('Not evaluated')),
            cons_status_national=Case(
                When(
                    taxonomy__national_conservation_status__isnull
                    =False,
                    then=F('taxonomy__iucn_status__category')),
                default=Value('Not evaluated')),
            endemism=Case(When(taxonomy__endemism__isnull=False,
                               then=F('taxonomy__endemism__name')),
                          default=Value('Unknown')),
        ).values(
            'taxon', 'origin', 'cons_status',
            'cons_status_national', 'endemism'
        ).annotate(
            count=Count('taxon')
        ).order_by('taxon')
        return list(occurrence_table_data)

    site_id = filters['siteId']
    times['process_search'] = time.time() - start_time

    # Indicates whether to show occurrence data per year (y) or per month (m)
    data_frequency = filters.get('d', PER_YEAR_FREQUENCY)

    iucn_category = dict(
        (x, y) for x, y in IUCNStatus.CATEGORY_CHOICES)

    origin_name_list = dict(
        (x, y) for x, y in Taxonomy.CATEGORY_CHOICES
    )

    if data_frequency == PER_MONTH_FREQUENCY:
        taxa_occurrence = site_taxa_occurrences_per_date(
            collection_results
        )
    else:
        taxa_occurrence = site_taxa_occurrences_per_year(
            collection_results)

    category_summary = collection_results.exclude(
        taxonomy__origin=''
    ).annotate(
        origin=F('taxonomy__origin')
    ).values_list(
        'origin'
    ).annotate(
        count=Count('taxonomy__origin')
    )
    is_multi_sites = False
    is_sass_exists = False

    if site_id:
        start_time = time.time()
        site_details = overview_site_detail(site_id)
        site_details['Species and Occurences'] = (
            get_number_of_records_and_taxa(collection_results))
        times['overview_site_detail'] = time.time() - start_time
    else:
        start_time = time.time()
        is_multi_sites = True
        site_details = multiple_site_details(collection_results)
        times['multiple_site_details'] = time.time() - start_time
        is_sass_exists = collection_results.filter(
            notes__icontains='sass'
        ).count() > 0
    search_process.set_search_raw_query(
        search.location_sites_raw_query
    )
    search_process.set_status(SEARCH_FINISHED, False)
    search_process.create_view()

    start_time = time.time()
    biodiversity_data = get_biodiversity_data(collection_results)
    site_images = []
    if not is_multi_sites:
        site_image_objects = SiteImage.objects.filter(
            Q(survey__in=list(
                collection_results.distinct('survey').values_list(
                    'survey__id', flat=True))) |
            Q(site_id=int(site_id))
        ).values_list(
            'image', flat=True
        )
        for site_image in site_image_objects:
            site_images.append(
                get_thumbnail(
                    site_image, 'x500', crop='center', quality=99).url
            )
    times['get_biodiversity_data'] = time.time() - start_time

    # Check module
    modules = []
    module_filter = filters.get('modules')
    if module_filter:
        module_ids = []
        if isinstance(module_filter, str):
            if ',' in module_filter:
                module_ids = [int(x) for x in module_filter.split(',') if x.isdigit()]
            elif module_filter.isdigit():
                module_ids = [int(module_filter)]
        if module_ids:
            modules = list(TaxonGroup.objects.filter(
                category=TaxonomicGroupCategory.SPECIES_MODULE.name,
                id__in=module_ids
            ).values_list('name', flat=True))

    # - Survey
    survey_list = []
    surveys = Survey.objects.filter(
        id__in=collection_results.values('survey')
    ).order_by('-date')
    for survey in surveys[:5]:
        survey_list.append({
            'date': str(survey.date),
            'site': str(survey.site),
            'id': survey.id,
            'records': (
                BiologicalCollectionRecord.objects.filter(
                    survey=survey).count()
            )
        })

    # - Source references
    start_time = time.time()
    collection_with_references = collection_results.exclude(
        source_reference__isnull=True
    ).distinct('source_reference')

    source_references = collection_with_references.source_references()
    times['source_references'] = time.time() - start_time

    # - Chemical data
    start_time = time.time()
    list_chems = {}
    chem_exist = False
    if site_id:
        list_chems_code = [
            'COND',
            'TEMP',
            'PH',
            'DO'
        ]
        chems = ChemicalRecord.objects.filter(
            Q(location_site_id=site_id) |
            Q(survey__site_id=site_id)
        )
        chems_source_references = chems.source_references()
        if chems_source_references:
            existing_ids = [
                ref['ID'] for ref in source_references
            ]
            for chem_source_reference in chems_source_references:
                if (
                        'ID' in chem_source_reference and
                        chem_source_reference['ID'] not in existing_ids
                ):
                    source_references.append(chem_source_reference)
        x_label = []
        if chems.count() > 0:
            chem_exist = True
        for chem in list_chems_code:
            chem_name = chem.lower().replace('-n', '').upper()
            qs = chems.filter(chem__chem_code=chem).order_by('date')
            if not qs:
                continue
            value = ChemicalRecordsSerializer(qs, many=True)
            # Get chemical unit
            chem_unit = qs[0].chem.chem_unit.unit
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
        list_chems['x_label'] = x_label

    times['chemical_records'] = time.time() - start_time

    try:
        dashboard_configuration = json.loads(
            DashboardConfiguration.objects.get(
                module_group__id=filters['modules']
            ).additional_data
        )
    except (
            DashboardConfiguration.DoesNotExist,
            KeyError,
            ValueError
    ):
        dashboard_configuration = {}

    response_data = {
        TOTAL_RECORDS: collection_results.count(),
        SITE_DETAILS: dict(site_details),
        TAXA_OCCURRENCE: dict(taxa_occurrence),
        CATEGORY_SUMMARY: dict(category_summary),
        OCCURRENCE_DATA: occurrence_data(collection_results),
        IUCN_NAME_LIST: iucn_category,
        ORIGIN_NAME_LIST: origin_name_list,
        BIODIVERSITY_DATA: dict(biodiversity_data),
        SOURCE_REFERENCES: source_references,
        CHEMICAL_RECORDS: list_chems,
        SURVEY: survey_list,
        'modules': modules,
        'site_images': list(site_images),
        'process': search_process.process_id,
        'extent': search.extent(),
        'sites_raw_query': search_process.process_id,
        'is_multi_sites': is_multi_sites,
        'is_sass_exists': is_sass_exists,
        'is_chem_exists': chem_exist,
        'total_survey': surveys.count(),
        'dashboard_configuration': dashboard_configuration,
        'times': times
    }

    if not called_directly:
        self.update_state(state='SUCCESS')

    create_search_process_file(
        response_data, search_process, file_path=None, finished=True)
    return response_data
