from django.contrib import admin, messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path

from climate.models import Climate, ClimateStation
from climate.utils import merge_climate_stations


@admin.register(Climate)
class ClimateAdmin(admin.ModelAdmin):
    """Admin interface for Climate model."""

    list_display = [
        'location_site',
        'station_name',
        'date',
        'avg_temperature',
        'daily_rainfall',
        'avg_humidity',
        'avg_windspeed',
        'flag'
    ]

    list_filter = [
        'year',
        'month',
        'station_name'
    ]

    search_fields = [
        'location_site__name',
        'location_site__site_code',
        'station_name'
    ]

    date_hierarchy = 'date'

    readonly_fields = ['created_at', 'updated_at', 'year', 'month', 'day']

    fieldsets = (
        ('Location Information', {
            'fields': ('location_site', 'station_name')
        }),
        ('Date Information', {
            'fields': ('date', 'year', 'month', 'day')
        }),
        ('Temperature Data (°C)', {
            'fields': ('avg_temperature', 'max_temperature', 'min_temperature')
        }),
        ('Humidity Data (%)', {
            'fields': ('avg_humidity', 'max_humidity', 'min_humidity')
        }),
        ('Other Measurements', {
            'fields': ('avg_windspeed', 'daily_rainfall', 'flag')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-date']

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('location_site')


@admin.register(ClimateStation)
class ClimateStationAdmin(admin.ModelAdmin):
    """Admin interface for merging climate stations (LocationSite proxy)."""

    list_display = ['name', 'site_code', 'latitude', 'longitude', 'climate_record_count']
    search_fields = ['name', 'site_code']
    actions = ['merge_stations_action']
    readonly_fields = ['site_code', 'latitude', 'longitude']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            Q(location_type__name__iexact='Weather Station') | Q(climate_data__isnull=False)
        ).distinct()

    def climate_record_count(self, obj):
        return obj.climate_data.count()
    climate_record_count.short_description = 'Records'

    def has_add_permission(self, request):
        return False

    def merge_stations_action(self, request, queryset):
        if queryset.count() < 2:
            self.message_user(
                request,
                'Select at least 2 stations to merge.',
                messages.ERROR
            )
            return
        selected = ','.join(str(pk) for pk in queryset.values_list('pk', flat=True))
        return HttpResponseRedirect(f'merge/?ids={selected}')
    merge_stations_action.short_description = 'Merge selected climate stations'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'merge/',
                self.admin_site.admin_view(self.merge_view),
                name='climate_climatestation_merge',
            ),
        ]
        return custom_urls + urls

    def merge_view(self, request):
        ids_param = request.GET.get('ids', '') or request.POST.get('ids', '')
        id_list = [
            int(i) for i in ids_param.split(',') if i.strip().isdigit()
        ]
        stations = ClimateStation.objects.filter(pk__in=id_list)

        if stations.count() < 2:
            self.message_user(
                request,
                'Select at least 2 stations to merge.',
                messages.ERROR
            )
            return HttpResponseRedirect('../')

        if request.method == 'POST':
            primary_id = request.POST.get('primary_station')
            if not primary_id:
                self.message_user(
                    request,
                    'Please select a primary station.',
                    messages.ERROR
                )
            else:
                try:
                    primary = ClimateStation.objects.get(pk=primary_id)
                except ClimateStation.DoesNotExist:
                    self.message_user(request, 'Primary station not found.', messages.ERROR)
                    return HttpResponseRedirect('../')

                secondaries = list(stations.exclude(pk=primary_id))
                secondary_count = len(secondaries)

                new_lat = request.POST.get('latitude', '').strip()
                new_lon = request.POST.get('longitude', '').strip()
                if new_lat and new_lon:
                    try:
                        from django.contrib.gis.geos import Point
                        lat = float(new_lat)
                        lon = float(new_lon)
                        primary.latitude = lat
                        primary.longitude = lon
                        primary.geometry_point = Point(lon, lat)
                        primary.save()
                    except (ValueError, Exception):
                        self.message_user(
                            request,
                            'Invalid coordinates - skipping coordinate update.',
                            messages.WARNING
                        )

                merge_climate_stations(primary, secondaries)
                self.message_user(
                    request,
                    f'Successfully merged {secondary_count} station(s) into "{primary.name}".',
                )
                return HttpResponseRedirect('../')

        context = {
            **self.admin_site.each_context(request),
            'title': 'Merge Climate Stations',
            'stations': stations,
            'ids': ids_param,
            'opts': self.model._meta,
        }
        return TemplateResponse(
            request,
            'admin/climate/climatestation/merge_stations.html',
            context,
        )
