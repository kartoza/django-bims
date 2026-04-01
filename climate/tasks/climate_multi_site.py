from celery import shared_task


@shared_task(
    name='climate.tasks.climate_multi_site_summary',
    queue='search'
)
def climate_multi_site_summary(parameters, search_process_id):
    from django.db.models import Avg, Min, Max, Sum, Count

    from bims.api_views.search_module import ClimateModule
    from bims.models import BaseMapLayer
    from bims.models.search_process import (
        SearchProcess,
        SEARCH_PROCESSING,
        SEARCH_FINISHED,
        SEARCH_FAILED,
    )
    from bims.utils.celery import memcache_lock

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    lock_id = '{0}-lock-{1}'.format(
        search_process.file_path,
        search_process.process_id,
    )
    oid = '{0}'.format(search_process.process_id)

    with memcache_lock(lock_id, oid) as acquired:
        if not acquired:
            return

        search_process.set_status(SEARCH_PROCESSING)

        try:
            search = ClimateModule(parameters)
            search.run_search()

            climate_qs = search.module
            location_sites = search.sites.order_by('site_code')

            summary = {
                'site_id': [],
                'site_code': [],
                'avg_temp': [],
                'min_temp': [],
                'max_temp': [],
                'avg_humidity': [],
                'avg_windspeed': [],
                'total_rainfall': [],
                'max_rainfall': [],
                'record_count': [],
            }

            coordinates = []

            for site in location_sites:
                qs = climate_qs.filter(location_site=site)
                if not qs.exists():
                    continue
                stats = qs.aggregate(
                    avg_temp=Avg('avg_temperature'),
                    min_temp=Min('min_temperature'),
                    max_temp=Max('max_temperature'),
                    avg_humidity=Avg('avg_humidity'),
                    avg_windspeed=Avg('avg_windspeed'),
                    total_rainfall=Sum('daily_rainfall'),
                    max_rainfall=Max('daily_rainfall'),
                    record_count=Count('id'),
                )
                summary['site_id'].append(site.id)
                summary['site_code'].append(
                    site.site_code if site.site_code else site.name
                )
                summary['avg_temp'].append(
                    round(stats['avg_temp'], 1) if stats['avg_temp'] is not None else None
                )
                summary['min_temp'].append(
                    round(stats['min_temp'], 1) if stats['min_temp'] is not None else None
                )
                summary['max_temp'].append(
                    round(stats['max_temp'], 1) if stats['max_temp'] is not None else None
                )
                summary['avg_humidity'].append(
                    round(stats['avg_humidity'], 1) if stats['avg_humidity'] is not None else None
                )
                summary['avg_windspeed'].append(
                    round(stats['avg_windspeed'], 2) if stats['avg_windspeed'] is not None else None
                )
                summary['total_rainfall'].append(
                    round(stats['total_rainfall'], 2) if stats['total_rainfall'] is not None else None
                )
                summary['max_rainfall'].append(
                    round(stats['max_rainfall'], 2) if stats['max_rainfall'] is not None else None
                )
                summary['record_count'].append(stats['record_count'])

                coordinates.append({
                    'x': site.get_centroid().x,
                    'y': site.get_centroid().y,
                })

            try:
                bing_map_key = BaseMapLayer.objects.get(source_type='bing').key
            except BaseMapLayer.DoesNotExist:
                bing_map_key = ''

            results = {
                'status': SEARCH_FINISHED,
                'climate_summary_data': summary,
                'coordinates': coordinates,
                'bing_map_key': bing_map_key,
            }

            search_process.set_status(SEARCH_FINISHED, False)
            search_process.save_to_file(results)

        except Exception:
            search_process.set_status(SEARCH_FAILED)
            raise
